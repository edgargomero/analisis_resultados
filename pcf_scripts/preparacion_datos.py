import streamlit as st
import pandas as pd
import json
import os
from pathlib import Path
from datetime import datetime
import requests
from typing import Dict, List, Optional, Union
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PreparadorDatos:
    """Maneja la preparación de datos desde múltiples fuentes"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.absolute()
        self.datos_path = self.base_path / "datos_preparados"
        self.datos_path.mkdir(exist_ok=True)
        
    def procesar_csv(self, archivo_cargado) -> pd.DataFrame:
        """Procesa archivo CSV cargado"""
        try:
            # Intentar diferentes encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            for encoding in encodings:
                try:
                    df = pd.read_csv(archivo_cargado, encoding=encoding)
                    logger.info(f"CSV procesado exitosamente con encoding {encoding}")
                    return df
                except UnicodeDecodeError:
                    continue
            
            raise Exception("No se pudo decodificar el archivo CSV")
            
        except Exception as e:
            logger.error(f"Error procesando CSV: {str(e)}")
            raise
    
    def procesar_xlsx(self, archivo_cargado) -> pd.DataFrame:
        """Procesa archivo Excel cargado"""
        try:
            df = pd.read_excel(archivo_cargado)
            logger.info("Excel procesado exitosamente")
            return df
        except Exception as e:
            logger.error(f"Error procesando Excel: {str(e)}")
            raise
    
    def procesar_json(self, archivo_cargado) -> pd.DataFrame:
        """Procesa archivo JSON cargado"""
        try:
            data = json.load(archivo_cargado)
            
            # Si es una lista de objetos, convertir directamente
            if isinstance(data, list):
                df = pd.DataFrame(data)
            # Si es un objeto con datos anidados
            elif isinstance(data, dict):
                # Buscar la clave que contiene los datos principales
                for key, value in data.items():
                    if isinstance(value, list):
                        df = pd.DataFrame(value)
                        break
                else:
                    # Si no hay listas, intentar convertir el dict directamente
                    df = pd.DataFrame([data])
            else:
                raise Exception("Formato JSON no reconocido")
            
            logger.info("JSON procesado exitosamente")
            return df
            
        except Exception as e:
            logger.error(f"Error procesando JSON: {str(e)}")
            raise
    
    def validar_datos_llamadas(self, df: pd.DataFrame) -> Dict[str, any]:
        """Valida que el DataFrame tenga las columnas necesarias para análisis de llamadas"""
        columnas_requeridas = {
            'fecha': ['fecha', 'date', 'fecha_llamada', 'call_date'],
            'hora': ['hora', 'time', 'hora_llamada', 'call_time'],
            'tipo': ['tipo', 'type', 'tipo_llamada', 'call_type', 'direccion'],
            'duracion': ['duracion', 'duration', 'duracion_segundos', 'call_duration'],
            'agente': ['agente', 'agent', 'usuario', 'user', 'operador']
        }
        
        columnas_encontradas = {}
        columnas_faltantes = []
        
        df_columns_lower = [col.lower() for col in df.columns]
        
        for campo, variantes in columnas_requeridas.items():
            encontrado = False
            for variante in variantes:
                if variante.lower() in df_columns_lower:
                    idx = df_columns_lower.index(variante.lower())
                    columnas_encontradas[campo] = df.columns[idx]
                    encontrado = True
                    break
            if not encontrado:
                columnas_faltantes.append(campo)
        
        return {
            'valido': len(columnas_faltantes) == 0,
            'columnas_encontradas': columnas_encontradas,
            'columnas_faltantes': columnas_faltantes,
            'total_registros': len(df)
        }
    
    def estandarizar_datos_llamadas(self, df: pd.DataFrame, mapeo_columnas: Dict[str, str]) -> pd.DataFrame:
        """Estandariza el DataFrame de llamadas al formato esperado"""
        df_estandar = pd.DataFrame()
        
        # Mapear columnas
        for campo_estandar, columna_original in mapeo_columnas.items():
            if columna_original in df.columns:
                df_estandar[campo_estandar] = df[columna_original]
        
        # Procesar fecha y hora
        if 'fecha' in df_estandar.columns:
            df_estandar['fecha'] = pd.to_datetime(df_estandar['fecha'], errors='coerce')
        
        # Asegurar tipo de llamada
        if 'tipo' in df_estandar.columns:
            df_estandar['tipo'] = df_estandar['tipo'].astype(str).str.lower()
            # Mapear valores comunes
            mapeo_tipos = {
                'incoming': 'entrante',
                'outgoing': 'saliente',
                'inbound': 'entrante',
                'outbound': 'saliente',
                'entrada': 'entrante',
                'salida': 'saliente'
            }
            df_estandar['tipo'] = df_estandar['tipo'].replace(mapeo_tipos)
        
        # Convertir duración a segundos si es necesario
        if 'duracion' in df_estandar.columns:
            df_estandar['duracion'] = pd.to_numeric(df_estandar['duracion'], errors='coerce')
        
        return df_estandar
    
    def guardar_datos_preparados(self, df: pd.DataFrame, nombre: str) -> str:
        """Guarda los datos preparados en el directorio de datos"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_archivo = f"{nombre}_{timestamp}.csv"
        ruta_completa = self.datos_path / nombre_archivo
        
        df.to_csv(ruta_completa, index=False, encoding='utf-8')
        logger.info(f"Datos guardados en: {ruta_completa}")
        
        return str(ruta_completa)


class IntegradorReservo:
    """Maneja la integración con la API de Reservo"""
    
    def __init__(self, api_key: Optional[str] = None, api_url: str = "https://reservo.cl/APIpublica/v2"):
        self.api_key = api_key
        self.api_url = api_url
        self.headers = {}
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'
    
    def test_conexion(self) -> bool:
        """Prueba la conexión con la API"""
        try:
            response = requests.get(
                f"{self.api_url}/api/schema/",
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error conectando con Reservo: {str(e)}")
            return False
    
    def obtener_citas(self, fecha_inicio: str, fecha_fin: str) -> Optional[pd.DataFrame]:
        """Obtiene las citas en un rango de fechas"""
        try:
            # Este endpoint es un ejemplo, necesitarás ajustarlo según la documentación real
            response = requests.get(
                f"{self.api_url}/citas",
                headers=self.headers,
                params={
                    'fecha_inicio': fecha_inicio,
                    'fecha_fin': fecha_fin
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return pd.DataFrame(data)
                elif isinstance(data, dict) and 'data' in data:
                    return pd.DataFrame(data['data'])
            else:
                logger.error(f"Error en API Reservo: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo citas de Reservo: {str(e)}")
            return None
    
    def obtener_profesionales(self) -> Optional[pd.DataFrame]:
        """Obtiene la lista de profesionales"""
        try:
            response = requests.get(
                f"{self.api_url}/profesionales",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return pd.DataFrame(data)
                elif isinstance(data, dict) and 'data' in data:
                    return pd.DataFrame(data['data'])
            else:
                logger.error(f"Error en API Reservo: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo profesionales de Reservo: {str(e)}")
            return None


def mostrar_preparacion_datos():
    """Muestra la interfaz de preparación de datos en Streamlit"""
    st.header("🔧 Preparación de Datos")
    
    preparador = PreparadorDatos()
    
    # Tabs para diferentes fuentes de datos
    tab_archivos, tab_api = st.tabs(["📁 Cargar Archivos", "🔌 API Reservo"])
    
    with tab_archivos:
        st.subheader("Cargar Archivos de Datos")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            archivo_cargado = st.file_uploader(
                "Selecciona un archivo",
                type=['csv', 'xlsx', 'xls', 'json'],
                help="Formatos soportados: CSV, Excel (XLSX/XLS), JSON"
            )
        
        with col2:
            tipo_datos = st.selectbox(
                "Tipo de datos",
                ["Llamadas", "Citas", "Usuarios", "Otro"]
            )
        
        if archivo_cargado is not None:
            try:
                # Determinar tipo de archivo y procesarlo
                nombre_archivo = archivo_cargado.name
                extension = nombre_archivo.split('.')[-1].lower()
                
                with st.spinner(f"Procesando archivo {nombre_archivo}..."):
                    if extension == 'csv':
                        df = preparador.procesar_csv(archivo_cargado)
                    elif extension in ['xlsx', 'xls']:
                        df = preparador.procesar_xlsx(archivo_cargado)
                    elif extension == 'json':
                        df = preparador.procesar_json(archivo_cargado)
                    else:
                        st.error(f"Formato no soportado: {extension}")
                        return
                
                st.success(f"✅ Archivo procesado: {len(df)} registros encontrados")
                
                # Mostrar vista previa
                with st.expander("Vista previa de datos", expanded=True):
                    st.dataframe(df.head(10))
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total de registros", len(df))
                    with col2:
                        st.metric("Columnas", len(df.columns))
                    with col3:
                        st.metric("Valores nulos", df.isnull().sum().sum())
                
                # Si son datos de llamadas, validar y estandarizar
                if tipo_datos == "Llamadas":
                    st.subheader("📞 Validación de Datos de Llamadas")
                    
                    validacion = preparador.validar_datos_llamadas(df)
                    
                    if validacion['valido']:
                        st.success("✅ Todas las columnas requeridas están presentes")
                        
                        # Mostrar mapeo de columnas
                        st.write("**Mapeo de columnas detectado:**")
                        for campo, columna in validacion['columnas_encontradas'].items():
                            st.write(f"- {campo}: `{columna}`")
                        
                        # Botón para estandarizar y guardar
                        if st.button("Estandarizar y Guardar Datos"):
                            df_estandar = preparador.estandarizar_datos_llamadas(
                                df, 
                                validacion['columnas_encontradas']
                            )
                            
                            ruta_guardado = preparador.guardar_datos_preparados(
                                df_estandar,
                                "llamadas_preparadas"
                            )
                            
                            st.success(f"✅ Datos guardados exitosamente")
                            st.info(f"Archivo: `{Path(ruta_guardado).name}`")
                            
                            # Mostrar resumen de datos estandarizados
                            with st.expander("Datos estandarizados"):
                                st.dataframe(df_estandar.head())
                                
                    else:
                        st.warning("⚠️ Faltan algunas columnas requeridas")
                        st.write("**Columnas faltantes:**")
                        for col in validacion['columnas_faltantes']:
                            st.write(f"- {col}")
                        
                        st.info("💡 Puedes continuar, pero algunas funcionalidades pueden estar limitadas")
                        
                        # Permitir mapeo manual
                        st.subheader("Mapeo Manual de Columnas")
                        
                        mapeo_manual = {}
                        columnas_disponibles = [''] + list(df.columns)
                        
                        for campo in ['fecha', 'hora', 'tipo', 'duracion', 'agente']:
                            mapeo_manual[campo] = st.selectbox(
                                f"Columna para {campo}",
                                columnas_disponibles,
                                key=f"map_{campo}"
                            )
                        
                        if st.button("Aplicar Mapeo Manual"):
                            # Filtrar mapeos vacíos
                            mapeo_final = {k: v for k, v in mapeo_manual.items() if v}
                            
                            if mapeo_final:
                                df_estandar = preparador.estandarizar_datos_llamadas(df, mapeo_final)
                                ruta_guardado = preparador.guardar_datos_preparados(
                                    df_estandar,
                                    "llamadas_preparadas_manual"
                                )
                                st.success(f"✅ Datos guardados con mapeo manual")
                            else:
                                st.error("Por favor selecciona al menos una columna para mapear")
                
                # Para otros tipos de datos
                else:
                    if st.button(f"Guardar Datos de {tipo_datos}"):
                        ruta_guardado = preparador.guardar_datos_preparados(
                            df,
                            tipo_datos.lower()
                        )
                        st.success(f"✅ Datos guardados exitosamente")
                        st.info(f"Archivo: `{Path(ruta_guardado).name}`")
                        
            except Exception as e:
                st.error(f"Error procesando archivo: {str(e)}")
                logger.error(f"Error en carga de archivo: {str(e)}")
    
    with tab_api:
        st.subheader("🔌 Integración con API Reservo")
        
        # Configuración de API
        with st.expander("⚙️ Configuración de API", expanded=True):
            api_key = st.text_input(
                "API Key de Reservo",
                type="password",
                help="Ingresa tu API Key de Reservo para conectarte"
            )
            
            if api_key:
                integrador = IntegradorReservo(api_key)
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button("Probar Conexión"):
                        with st.spinner("Probando conexión..."):
                            if integrador.test_conexion():
                                st.success("✅ Conexión exitosa")
                            else:
                                st.error("❌ No se pudo conectar. Verifica tu API Key")
        
        if api_key:
            st.subheader("📅 Obtener Datos de Citas")
            
            col1, col2 = st.columns(2)
            with col1:
                fecha_inicio = st.date_input("Fecha inicio")
            with col2:
                fecha_fin = st.date_input("Fecha fin")
            
            if st.button("Obtener Citas"):
                with st.spinner("Obteniendo datos de Reservo..."):
                    df_citas = integrador.obtener_citas(
                        fecha_inicio.strftime('%Y-%m-%d'),
                        fecha_fin.strftime('%Y-%m-%d')
                    )
                    
                    if df_citas is not None and not df_citas.empty:
                        st.success(f"✅ {len(df_citas)} citas obtenidas")
                        
                        with st.expander("Vista previa de citas"):
                            st.dataframe(df_citas.head())
                        
                        if st.button("Guardar Citas"):
                            ruta_guardado = preparador.guardar_datos_preparados(
                                df_citas,
                                "citas_reservo"
                            )
                            st.success(f"✅ Citas guardadas exitosamente")
                    else:
                        st.warning("No se encontraron citas en el período seleccionado")
            
            st.subheader("👥 Obtener Profesionales")
            
            if st.button("Obtener Lista de Profesionales"):
                with st.spinner("Obteniendo profesionales..."):
                    df_prof = integrador.obtener_profesionales()
                    
                    if df_prof is not None and not df_prof.empty:
                        st.success(f"✅ {len(df_prof)} profesionales obtenidos")
                        
                        with st.expander("Lista de profesionales"):
                            st.dataframe(df_prof)
                        
                        if st.button("Guardar Profesionales"):
                            ruta_guardado = preparador.guardar_datos_preparados(
                                df_prof,
                                "profesionales_reservo"
                            )
                            st.success(f"✅ Profesionales guardados exitosamente")
                    else:
                        st.warning("No se pudieron obtener los profesionales")
        
        # Información sobre la API
        with st.expander("ℹ️ Información sobre la API de Reservo"):
            st.write("""
            La API de Reservo permite obtener:
            - **Citas**: Información sobre citas agendadas
            - **Profesionales**: Lista de profesionales disponibles
            - **Pacientes**: Información de pacientes (requiere permisos)
            - **Servicios**: Catálogo de servicios ofrecidos
            
            Para obtener tu API Key:
            1. Ingresa a tu cuenta de Reservo
            2. Ve a Configuración > API
            3. Genera o copia tu API Key
            
            [Ver documentación completa](https://reservo.cl/APIpublica/v2/documentacion/)
            """)
    
    # Sección de datos preparados
    st.divider()
    st.subheader("📊 Datos Preparados Disponibles")
    
    # Listar archivos en el directorio de datos preparados
    if preparador.datos_path.exists():
        archivos = list(preparador.datos_path.glob("*.csv"))
        
        if archivos:
            df_archivos = pd.DataFrame([
                {
                    'Archivo': f.name,
                    'Tamaño': f"{f.stat().st_size / 1024:.1f} KB",
                    'Modificado': datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
                    'Ruta': str(f)
                }
                for f in archivos
            ])
            
            st.dataframe(
                df_archivos[['Archivo', 'Tamaño', 'Modificado']],
                use_container_width=True
            )
            
            # Opción para cargar archivo preparado
            archivo_seleccionado = st.selectbox(
                "Seleccionar archivo para vista previa",
                options=archivos,
                format_func=lambda x: x.name
            )
            
            if archivo_seleccionado:
                if st.button("Ver Vista Previa"):
                    df_preview = pd.read_csv(archivo_seleccionado)
                    st.dataframe(df_preview.head(10))
        else:
            st.info("No hay archivos preparados aún. Carga un archivo para comenzar.")
    else:
        preparador.datos_path.mkdir(exist_ok=True)
        st.info("No hay archivos preparados aún. Carga un archivo para comenzar.")