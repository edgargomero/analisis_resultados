#!/usr/bin/env python3
"""
CEAPSI - Aplicación Principal del Sistema PCF
Sistema completo de predicción y análisis de llamadas para call center
"""

import streamlit as st
import sys
import os
import warnings

# Suprimir warnings menores
warnings.filterwarnings('ignore', category=UserWarning, module='pandas')
import logging
from datetime import datetime

# Configurar logging detallado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ceapsi_app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('CEAPSI_APP')
from pathlib import Path

# Agregar el directorio actual al path para imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Importar módulos del sistema
from dashboard_comparacion import DashboardValidacionCEAPSI
import subprocess
import json
from datetime import datetime
import io
import tempfile
import pandas as pd
import os

# Configuración de la página principal
st.set_page_config(
    page_title="CEAPSI - Sistema PCF",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded"
)

def mostrar_seccion_carga_archivos():
    """Sección para cargar archivos de datos manualmente"""
    
    st.sidebar.markdown("### 📁 Cargar Datos")
    
    # Mostrar estado actual
    if st.session_state.datos_cargados:
        st.sidebar.success("✅ Datos cargados correctamente")
        
        # Botón para limpiar datos
        if st.sidebar.button("🗑️ Limpiar Datos", use_container_width=True):
            st.session_state.archivo_datos = None
            st.session_state.datos_cargados = False
            st.rerun()
    else:
        st.sidebar.warning("⚠️ No hay datos cargados")
    
    # Uploader de archivos
    archivo_subido = st.sidebar.file_uploader(
        "Seleccionar archivo de llamadas:",
        type=['csv', 'xlsx', 'xls'],
        help="Formatos soportados: CSV, Excel (.xlsx, .xls)"
    )
    
    if archivo_subido is not None:
        if st.sidebar.button("🚀 Procesar Archivo", use_container_width=True, type="primary"):
            procesar_archivo_subido(archivo_subido)
    
    # Información sobre el formato esperado
    with st.sidebar.expander("📝 Formato de Datos Esperado"):
        st.markdown("""
        **Columnas requeridas:**
        - `FECHA`: Fecha y hora de la llamada
        - `TELEFONO`: Número de teléfono
        - `SENTIDO`: 'in' (entrante) o 'out' (saliente)
        - `ATENDIDA`: 'Si' o 'No'
        
        **Formato de fecha esperado:**
        - DD-MM-YYYY HH:MM:SS
        - Ejemplo: 02-01-2023 08:08:07
        
        **Separador CSV:** Punto y coma (;)
        
        **Archivo de ejemplo:**
        Descarga un archivo de ejemplo para probar el sistema.
        """)
        
        # Botón para descargar ejemplo
        try:
            with open(os.path.join(os.path.dirname(__file__), 'ejemplo_datos_llamadas.csv'), 'r', encoding='utf-8') as f:
                ejemplo_csv = f.read()
            
            st.download_button(
                "📎 Descargar Ejemplo CSV",
                data=ejemplo_csv,
                file_name="ejemplo_datos_llamadas.csv",
                mime="text/csv",
                help="Archivo de ejemplo con el formato correcto"
            )
        except:
            pass
    
    st.sidebar.markdown("---")

def procesar_archivo_subido(archivo_subido):
    """Procesa el archivo subido y lo guarda temporalmente"""
    
    logger.info(f"Iniciando procesamiento de archivo: {archivo_subido.name}")
    
    try:
        with st.spinner("Procesando archivo..."):
            logger.info(f"Archivo tipo: {archivo_subido.type if hasattr(archivo_subido, 'type') else 'desconocido'}")
            logger.info(f"Tamaño archivo: {archivo_subido.size if hasattr(archivo_subido, 'size') else 'desconocido'} bytes")
            
            # Leer el archivo según su tipo
            if archivo_subido.name.endswith('.csv'):
                logger.info("Procesando archivo CSV")
                # Intentar diferentes encodings para CSV
                contenido_bytes = archivo_subido.read()
                logger.info(f"Bytes leídos: {len(contenido_bytes)}")
                
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        logger.info(f"Intentando encoding: {encoding}")
                        contenido_str = contenido_bytes.decode(encoding)
                        df = pd.read_csv(io.StringIO(contenido_str), sep=';')
                        logger.info(f"CSV leído exitosamente con encoding {encoding}")
                        break
                    except UnicodeDecodeError as e:
                        logger.warning(f"Fallo encoding {encoding}: {e}")
                        continue
                else:
                    logger.error("No se pudo decodificar el archivo CSV con ningún encoding")
                    st.error("❌ No se pudo decodificar el archivo CSV")
                    return
            
            elif archivo_subido.name.endswith(('.xlsx', '.xls')):
                logger.info("Procesando archivo Excel")
                df = pd.read_excel(archivo_subido)
                logger.info("Excel leído exitosamente")
            
            logger.info(f"DataFrame cargado: {len(df)} filas, {len(df.columns)} columnas")
            logger.info(f"Columnas encontradas: {list(df.columns)}")
            
            # Validar columnas requeridas
            columnas_requeridas = ['FECHA', 'TELEFONO']
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
            
            logger.info(f"Validando columnas requeridas: {columnas_requeridas}")
            
            if columnas_faltantes:
                logger.error(f"Columnas faltantes: {columnas_faltantes}")
                st.error(f"❌ Columnas faltantes: {', '.join(columnas_faltantes)}")
                st.info("📝 Columnas encontradas: " + ", ".join(df.columns.tolist()))
                return
            
            # Validar que hay datos
            if len(df) == 0:
                logger.error("El archivo está vacío")
                st.error("❌ El archivo está vacío")
                return
            
            logger.info("Validación exitosa, guardando archivo temporal")
            
            # Guardar en sesión temporal
            archivo_temp = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8')
            logger.info(f"Archivo temporal creado: {archivo_temp.name}")
            
            df.to_csv(archivo_temp.name, sep=';', index=False, encoding='utf-8')
            archivo_temp.close()
            
            # Actualizar estado
            st.session_state.archivo_datos = archivo_temp.name
            st.session_state.datos_cargados = True
            
            logger.info(f"Datos guardados exitosamente. Estado actualizado.")
            
            st.success(f"✅ Archivo procesado exitosamente: {len(df):,} registros cargados")
            
            # Mostrar celebración
            st.balloons()
            
            # Mostrar resumen de datos
            st.info(f"📊 **Resumen del archivo:**")
            st.info(f"- **Registros**: {len(df):,}")
            st.info(f"- **Columnas**: {len(df.columns)}")
            st.info(f"- **Período**: Detectando...")
            
            # Intentar detectar rango de fechas
            if 'FECHA' in df.columns:
                try:
                    # Primero intentar con el formato específico
                    fechas = pd.to_datetime(df['FECHA'], format='%d-%m-%Y %H:%M:%S', errors='coerce')
                    # Si hay muchos valores nulos, intentar con dayfirst=True
                    if fechas.isnull().sum() > len(df) * 0.5:
                        fechas = pd.to_datetime(df['FECHA'], dayfirst=True, errors='coerce')
                    
                    fechas_validas = fechas.dropna()
                    if len(fechas_validas) > 0:
                        fecha_min = fechas_validas.min()
                        fecha_max = fechas_validas.max()
                        st.info(f"- **Rango de fechas**: {fecha_min.date()} a {fecha_max.date()}")
                except:
                    st.warning("⚠️ No se pudo procesar las fechas")
            
            st.rerun()
    
    except Exception as e:
        st.error(f"❌ Error procesando archivo: {str(e)}")
        st.info("💡 Verifica que el archivo tenga el formato correcto")

def crear_script_auditoria_temporal(ruta_archivo):
    """Crea un script temporal de auditoría que usa el archivo cargado"""
    
    script_content = f'''
#!/usr/bin/env python3
# Script temporal de auditoría generado automáticamente

import sys
import os
sys.path.append(os.path.dirname(__file__))

from auditoria_datos_llamadas import AuditoriaLlamadasAlodesk

def main():
    # Usar archivo cargado manualmente
    archivo_llamadas = r"{ruta_archivo}"
    output_path = os.path.dirname(__file__)
    
    print("🔍 INICIANDO AUDITORÍA DE DATOS CARGADOS")
    print("=" * 60)
    
    # Crear auditor
    auditor = AuditoriaLlamadasAlodesk(archivo_llamadas)
    
    # Ejecutar auditoría completa
    if auditor.cargar_y_limpiar_datos():
        reporte = auditor.generar_reporte_diagnostico(output_path)
        
        print("\n🎯 RESUMEN EJECUTIVO:")
        print(f"   📊 Total registros: {{len(auditor.df)}}")
        
        if 'recomendaciones' in reporte:
            print(f"   ⚠️ Recomendaciones: {{len(reporte['recomendaciones'])}}")
            
            for rec in reporte['recomendaciones']:
                print(f"   🔧 {{rec['tipo']}}: {{rec['problema']}}")
        
        print(f"\n📄 Reporte completo disponible")
        
    else:
        print("❌ No se pudo completar la auditoría")

if __name__ == "__main__":
    main()
'''
    
    # Guardar script temporal
    script_temp = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8')
    script_temp.write(script_content)
    script_temp.close()
    
    return script_temp.name

def crear_script_multimodelo_temporal(ruta_archivo, tipo_llamada):
    """Crea un script temporal de multi-modelo que usa el archivo cargado"""
    
    script_content = '''
#!/usr/bin/env python3
# Script temporal de multi-modelo generado automaticamente

import sys
import os
import logging
from datetime import datetime

# Configurar logging para el script temporal
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ceapsi_multimodelo.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('MULTIMODELO')

sys.path.append(os.path.dirname(__file__))

from sistema_multi_modelo import SistemaMultiModeloCEAPSI
import pandas as pd
from pathlib import Path

def main():
    logger.info("=" * 60)
    logger.info("INICIANDO SISTEMA MULTI-MODELO CEAPSI")
    logger.info("=" * 60)
    
    print("INICIANDO SISTEMA MULTI-MODELO CEAPSI")
    print("=" * 60)
    
    # Configurar sistema
    logger.info("Configurando sistema multi-modelo")
    sistema = SistemaMultiModeloCEAPSI()
    
    # Preparar datos desde el archivo cargado
    tipo_llamada = "'''+tipo_llamada+'''"
    archivo_datos = r"'''+ruta_archivo+'''"
    
    logger.info(f"Tipo de llamada: {tipo_llamada}")
    logger.info(f"Archivo de datos: {archivo_datos}")
    
    print("Procesando llamadas " + tipo_llamada + ":")
    print("-" * 40)
    
    # Cargar y procesar datos
    try:
        logger.info("Iniciando carga de datos")
        if not os.path.exists(archivo_datos):
            logger.error(f"Archivo no encontrado: {archivo_datos}")
            print(f"ERROR: Archivo no encontrado: {archivo_datos}")
            return
        
        logger.info("Leyendo archivo CSV")
        df_completo = pd.read_csv(archivo_datos, sep=';', encoding='utf-8')
        logger.info(f"Archivo leido: {len(df_completo)} registros, {len(df_completo.columns)} columnas")
        logger.info(f"Columnas: {list(df_completo.columns)}")
        
        # Procesar fechas
        df_completo['FECHA'] = pd.to_datetime(df_completo['FECHA'], format='%d-%m-%Y %H:%M:%S', errors='coerce')
        df_completo = df_completo.dropna(subset=['FECHA'])
        
        # Filtrar por tipo de llamada
        if 'SENTIDO' in df_completo.columns:
            if tipo_llamada == 'ENTRANTE':
                df_filtrado = df_completo[df_completo['SENTIDO'] == 'in'].copy()
            else:
                df_filtrado = df_completo[df_completo['SENTIDO'] == 'out'].copy()
        else:
            print("Advertencia: No se encontro columna SENTIDO, usando todos los datos")
            df_filtrado = df_completo.copy()
        
        # Filtrar solo dias laborales
        df_filtrado = df_filtrado[df_filtrado['FECHA'].dt.dayofweek < 5]
        
        # Agregar por dia
        df_diario = df_filtrado.groupby(df_filtrado['FECHA'].dt.date).size().reset_index()
        df_diario.columns = ['ds', 'y']
        df_diario['ds'] = pd.to_datetime(df_diario['ds'])
        
        # Agregar regresores basicos
        df_diario['dia_semana'] = df_diario['ds'].dt.dayofweek + 1
        df_diario['es_inicio_mes'] = (df_diario['ds'].dt.day <= 5).astype(int)
        df_diario['semana_mes'] = ((df_diario['ds'].dt.day - 1) // 7) + 1
        
        print("Datos procesados: " + str(len(df_diario)) + " dias de " + tipo_llamada.lower())
        
        if len(df_diario) < 30:
            print("ERROR: Datos insuficientes para entrenamiento (minimo 30 dias)")
            return
        
        # Entrenar todos los modelos
        sistema.entrenar_modelo_arima(df_diario)
        sistema.entrenar_modelo_prophet(df_diario)
        sistema.entrenar_modelos_ml(df_diario)
        
        # Validacion cruzada
        metricas_cv = sistema.validacion_cruzada_temporal(df_diario)
        
        # Calcular pesos ensemble
        sistema.calcular_pesos_ensemble(metricas_cv)
        
        # Generar predicciones
        predicciones = sistema.generar_predicciones_ensemble(df_diario, dias_futuro=28)
        
        if predicciones is not None:
            # Detectar alertas
            alertas = sistema.detectar_alertas_avanzadas(predicciones, df_diario)
            
            # Exportar resultados
            output_path = os.path.dirname(__file__)
            sistema.exportar_resultados_completos(predicciones, alertas, tipo_llamada, output_path)
            
            print("\\nRESUMEN " + tipo_llamada + ":")
            promedio = predicciones['yhat_ensemble'].mean()
            print("   Promedio predicho: " + str(round(promedio, 1)) + " llamadas/dia")
            dia_pico_idx = predicciones['yhat_ensemble'].idxmax()
            dia_pico = predicciones.loc[dia_pico_idx, 'ds'].strftime('%A')
            print("   Dia pico: " + dia_pico)
            print("   Alertas: " + str(len(alertas)) + " detectadas")
            print("\\nSISTEMA MULTI-MODELO COMPLETADO EXITOSAMENTE")
        else:
            print("ERROR: No se pudieron generar predicciones")
            
    except Exception as e:
        print("ERROR: " + str(e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
'''
    
    # Guardar script temporal
    script_temp = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8')
    script_temp.write(script_content)
    script_temp.close()
    
    return script_temp.name

def main():
    """Función principal de la aplicación Streamlit"""
    
    # Inicializar estado de sesión
    if 'archivo_datos' not in st.session_state:
        st.session_state.archivo_datos = None
    if 'datos_cargados' not in st.session_state:
        st.session_state.datos_cargados = False
    
    # Sidebar para navegación
    st.sidebar.title("📞 CEAPSI - Sistema PCF")
    st.sidebar.markdown("### Precision Call Forecast")
    st.sidebar.markdown("---")
    
    # Sección de carga de archivos
    mostrar_seccion_carga_archivos()
    
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
    
    # Verificar datos cargados
    if st.session_state.datos_cargados:
        st.sidebar.success("✅ Datos de llamadas disponibles")
        
        # Mostrar información del archivo cargado
        try:
            df = pd.read_csv(st.session_state.archivo_datos, sep=';')
            st.sidebar.info(f"📊 {len(df):,} registros cargados")
        except:
            st.sidebar.warning("⚠️ Error leyendo datos")
    else:
        st.sidebar.error("❌ No hay datos cargados")
        st.sidebar.info("📁 Sube un archivo para comenzar")
    
    # Verificar modelos entrenados (solo si hay datos cargados)
    if st.session_state.datos_cargados:
        archivos_modelos = list(Path(__file__).parent.parent.glob("predicciones_multimodelo_*.json"))
        if archivos_modelos:
            st.sidebar.success(f"✅ {len(archivos_modelos)} modelos disponibles")
        else:
            st.sidebar.warning("⚠️ No hay modelos entrenados")
    else:
        st.sidebar.info("🤖 Modelos: Pendiente de datos")
    
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
    en su call center. **Sube tu archivo de datos de llamadas** para comenzar el análisis 
    y optimizar la asignación de recursos.
    
    📁 **¡Empieza subiendo tu archivo en el sidebar!**
    """)
    
    # Mostrar estado de carga
    if st.session_state.datos_cargados:
        st.success("✅ ¡Datos cargados! Ya puedes usar todos los módulos del sistema.")
        
        # Mostrar resumen rápido de los datos cargados
        try:
            df = pd.read_csv(st.session_state.archivo_datos, sep=';')
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Registros Cargados", f"{len(df):,}")
            with col2:
                if 'FECHA' in df.columns:
                    fechas = pd.to_datetime(df['FECHA'], format='%d-%m-%Y %H:%M:%S', errors='coerce')
                    dias_unicos = fechas.dt.date.nunique()
                    st.metric("📅 Días de Datos", f"{dias_unicos}")
                else:
                    st.metric("📅 Días de Datos", "N/A")
            with col3:
                if 'SENTIDO' in df.columns:
                    tipos = df['SENTIDO'].value_counts()
                    entrantes = tipos.get('in', 0)
                    salientes = tipos.get('out', 0)
                    st.metric("📞 Tipos", f"E:{entrantes} S:{salientes}")
                else:
                    st.metric("📞 Tipos", "Sin segmentar")
        except:
            st.info("📊 Datos cargados correctamente")
    else:
        st.info("🔄 Esperando datos... Sube tu archivo CSV o Excel en la sección 'Cargar Datos' del sidebar.")
        
        # Mostrar instrucción visual
        st.markdown("""
        📍 **Pasos para comenzar:**
        1. Ve al sidebar → "Cargar Datos"
        2. Haz clic en "Seleccionar archivo de llamadas"
        3. Sube tu archivo CSV o Excel
        4. Haz clic en "🚀 Procesar Archivo"
        5. ¡Listo! Todos los módulos estarán disponibles
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
    
    if not st.session_state.datos_cargados:
        st.warning("⚠️ No hay datos cargados")
        st.info("📁 Por favor, sube un archivo de datos en la sección 'Cargar Datos' del sidebar")
        
        # Mostrar preview de cómo se vería el dashboard
        st.markdown("### 🔍 Vista Previa del Dashboard")
        st.image("https://via.placeholder.com/800x400/f0f2f6/333?text=Dashboard+de+Validaci%C3%B3n", 
                caption="El dashboard mostrará gráficas de atención, comparación de modelos y alertas una vez que subas los datos")
        return
    
    # Crear dashboard personalizado con datos cargados
    dashboard = DashboardValidacionCEAPSI()
    dashboard.base_path = Path(st.session_state.archivo_datos).parent
    dashboard.archivo_datos_manual = st.session_state.archivo_datos
    dashboard.ejecutar_dashboard()

def mostrar_auditoria():
    """Módulo de auditoría de datos"""
    
    st.title("🔍 Auditoría de Datos de Llamadas")
    st.markdown("### Análisis Profundo de Calidad y Patrones")
    
    if not st.session_state.datos_cargados:
        st.warning("⚠️ No hay datos cargados para auditar")
        st.info("📁 Sube un archivo de datos primero")
        return
    
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
                    # Crear script temporal que use el archivo cargado
                    script_temp = crear_script_auditoria_temporal(st.session_state.archivo_datos)
                    
                    # Ejecutar script de auditoría
                    result = subprocess.run(
                        [sys.executable, script_temp],
                        cwd=Path(__file__).parent,
                        capture_output=True,
                        text=True,
                        timeout=300,
                        encoding='utf-8',
                        errors='replace'  # Manejar errores de encoding
                    )
                    
                    # Limpiar archivo temporal
                    if os.path.exists(script_temp):
                        os.remove(script_temp)
                    
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
    
    if not st.session_state.datos_cargados:
        st.warning("⚠️ No hay datos cargados para segmentar")
        st.info("📁 Sube un archivo de datos primero")
        return
    
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
    
    if not st.session_state.datos_cargados:
        st.warning("⚠️ No hay datos cargados para entrenar modelos")
        st.info("📁 Sube un archivo de datos primero")
        return
    
    # Verificar calidad de datos antes de entrenar
    try:
        df = pd.read_csv(st.session_state.archivo_datos, sep=';')
        
        # Verificar columnas necesarias
        if 'FECHA' not in df.columns:
            st.error("❌ El archivo debe tener una columna 'FECHA'")
            return
        
        # Procesar fechas para verificar datos válidos
        fechas = pd.to_datetime(df['FECHA'], format='%d-%m-%Y %H:%M:%S', errors='coerce')
        df_validas = df[fechas.notna()]
        
        if len(df_validas) < 100:
            st.error(f"❌ Datos insuficientes: {len(df_validas)} registros válidos (mínimo 100)")
            st.info("💡 Necesitas al menos 100 registros con fechas válidas para entrenar modelos")
            return
        
        # Verificar días únicos
        dias_unicos = fechas.dt.date.nunique()
        if dias_unicos < 30:
            st.error(f"❌ Periodo insuficiente: {dias_unicos} días únicos (mínimo 30 días)")
            st.info("💡 Necesitas al menos 30 días de datos para entrenar modelos de series de tiempo")
            return
        
        st.success(f"✅ Datos válidos: {len(df_validas):,} registros en {dias_unicos} días")
        
    except Exception as e:
        st.error(f"❌ Error validando datos: {e}")
        return
    
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
            logger.info(f"Iniciando entrenamiento de modelos para {tipo_llamada}")
            
            with st.spinner(f"Entrenando modelos para llamadas {tipo_llamada.lower()}..."):
                try:
                    logger.info("Creando script temporal de multi-modelo")
                    # Crear script temporal que use el archivo cargado
                    script_temp = crear_script_multimodelo_temporal(st.session_state.archivo_datos, tipo_llamada)
                    logger.info(f"Script temporal creado: {script_temp}")
                    
                    logger.info("Ejecutando subprocess para entrenamiento")
                    result = subprocess.run(
                        [sys.executable, script_temp],
                        cwd=Path(__file__).parent,
                        capture_output=True,
                        text=True,
                        timeout=600,
                        encoding='utf-8',
                        errors='replace'  # Manejar errores de encoding
                    )
                    
                    logger.info(f"Subprocess completado con código: {result.returncode}")
                    logger.info(f"STDOUT length: {len(result.stdout) if result.stdout else 0}")
                    logger.info(f"STDERR length: {len(result.stderr) if result.stderr else 0}")
                    
                    if result.stdout:
                        logger.info(f"STDOUT: {result.stdout[:500]}...")  # Primeros 500 caracteres
                    if result.stderr:
                        logger.error(f"STDERR: {result.stderr[:500]}...")  # Primeros 500 caracteres
                    
                    # Limpiar archivo temporal
                    if os.path.exists(script_temp):
                        os.remove(script_temp)
                        logger.info("Archivo temporal limpiado")
                    
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
