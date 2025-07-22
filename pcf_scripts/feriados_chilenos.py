#!/usr/bin/env python3
"""
Módulo de Feriados Chilenos para CEAPSI
Gestiona y analiza patrones de llamadas considerando feriados nacionales chilenos
"""

import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta, date
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Tuple, Optional
import logging

# Configurar logging
logger = logging.getLogger(__name__)

class GestorFeriadosChilenos:
    """Gestor de feriados chilenos para análisis de datos de call center"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.absolute()
        self.feriados_df = None
        self.feriados_dict = {}
        self.cargar_feriados()
    
    def cargar_feriados(self):
        """Carga los feriados chilenos desde el archivo CSV"""
        try:
            # Intentar cargar desde el directorio de descargas del usuario
            rutas_posibles = [
                Path(r"C:\Users\edgar\Downloads\feriadoschile.csv"),
                self.base_path / "feriadoschile.csv",
                self.base_path / "data" / "feriadoschile.csv"
            ]
            
            archivo_encontrado = None
            for ruta in rutas_posibles:
                if ruta.exists():
                    archivo_encontrado = ruta
                    break
            
            if archivo_encontrado:
                self.feriados_df = pd.read_csv(archivo_encontrado)
                logger.info(f"Feriados cargados desde: {archivo_encontrado}")
            else:
                # Crear datos de feriados por defecto si no se encuentra el archivo
                self.crear_feriados_default()
                logger.warning("Archivo de feriados no encontrado, usando datos por defecto")
            
            # Procesar y normalizar datos
            self.procesar_feriados()
            
        except Exception as e:
            logger.error(f"Error cargando feriados: {e}")
            self.crear_feriados_default()
            self.procesar_feriados()
    
    def crear_feriados_default(self):
        """Crea un conjunto básico de feriados chilenos si no se encuentra el archivo"""
        feriados_default = [
            {"Fecha (dd-mm-yyyy)": "01-01-2024", "Descripcion feriado": "Año Nuevo"},
            {"Fecha (dd-mm-yyyy)": "29-03-2024", "Descripcion feriado": "Viernes Santo"},
            {"Fecha (dd-mm-yyyy)": "30-03-2024", "Descripcion feriado": "Sábado Santo"},
            {"Fecha (dd-mm-yyyy)": "01-05-2024", "Descripcion feriado": "Día Nacional del Trabajo"},
            {"Fecha (dd-mm-yyyy)": "21-05-2024", "Descripcion feriado": "Día de las Glorias Navales"},
            {"Fecha (dd-mm-yyyy)": "20-06-2024", "Descripcion feriado": "Día Nacional de los Pueblos Indígenas"},
            {"Fecha (dd-mm-yyyy)": "16-07-2024", "Descripcion feriado": "Día de la Virgen del Carmen"},
            {"Fecha (dd-mm-yyyy)": "15-08-2024", "Descripcion feriado": "Asunción de la Virgen"},
            {"Fecha (dd-mm-yyyy)": "18-09-2024", "Descripcion feriado": "Independencia Nacional"},
            {"Fecha (dd-mm-yyyy)": "19-09-2024", "Descripcion feriado": "Día de las Glorias del Ejército"},
            {"Fecha (dd-mm-yyyy)": "12-10-2024", "Descripcion feriado": "Encuentro de Dos Mundos"},
            {"Fecha (dd-mm-yyyy)": "31-10-2024", "Descripcion feriado": "Día de las Iglesias Evangélicas y Protestantes"},
            {"Fecha (dd-mm-yyyy)": "01-11-2024", "Descripcion feriado": "Día de Todos los Santos"},
            {"Fecha (dd-mm-yyyy)": "08-12-2024", "Descripcion feriado": "Inmaculada Concepción"},
            {"Fecha (dd-mm-yyyy)": "25-12-2024", "Descripcion feriado": "Navidad"},
            # 2025
            {"Fecha (dd-mm-yyyy)": "01-01-2025", "Descripcion feriado": "Año Nuevo"},
            {"Fecha (dd-mm-yyyy)": "18-04-2025", "Descripcion feriado": "Viernes Santo"},
            {"Fecha (dd-mm-yyyy)": "19-04-2025", "Descripcion feriado": "Sábado Santo"},
            {"Fecha (dd-mm-yyyy)": "01-05-2025", "Descripcion feriado": "Día Nacional del Trabajo"},
            {"Fecha (dd-mm-yyyy)": "21-05-2025", "Descripcion feriado": "Día de las Glorias Navales"},
            {"Fecha (dd-mm-yyyy)": "20-06-2025", "Descripcion feriado": "Día Nacional de los Pueblos Indígenas"},
            {"Fecha (dd-mm-yyyy)": "16-07-2025", "Descripcion feriado": "Día de la Virgen del Carmen"},
            {"Fecha (dd-mm-yyyy)": "15-08-2025", "Descripcion feriado": "Asunción de la Virgen"},
            {"Fecha (dd-mm-yyyy)": "18-09-2025", "Descripcion feriado": "Independencia Nacional"},
            {"Fecha (dd-mm-yyyy)": "19-09-2025", "Descripcion feriado": "Día de las Glorias del Ejército"},
            {"Fecha (dd-mm-yyyy)": "12-10-2025", "Descripcion feriado": "Encuentro de Dos Mundos"},
            {"Fecha (dd-mm-yyyy)": "31-10-2025", "Descripcion feriado": "Día de las Iglesias Evangélicas y Protestantes"},
            {"Fecha (dd-mm-yyyy)": "01-11-2025", "Descripcion feriado": "Día de Todos los Santos"},
            {"Fecha (dd-mm-yyyy)": "08-12-2025", "Descripcion feriado": "Inmaculada Concepción"},
            {"Fecha (dd-mm-yyyy)": "25-12-2025", "Descripcion feriado": "Navidad"}
        ]
        
        self.feriados_df = pd.DataFrame(feriados_default)
    
    def procesar_feriados(self):
        """Procesa y normaliza los datos de feriados"""
        if self.feriados_df is not None:
            # Convertir fechas
            self.feriados_df['fecha'] = pd.to_datetime(
                self.feriados_df['Fecha (dd-mm-yyyy)'], 
                format='%d-%m-%Y'
            )
            
            # Normalizar descripción
            self.feriados_df['descripcion'] = self.feriados_df['Descripcion feriado'].str.strip()
            
            # Crear campos adicionales
            self.feriados_df['año'] = self.feriados_df['fecha'].dt.year
            self.feriados_df['mes'] = self.feriados_df['fecha'].dt.month
            self.feriados_df['dia_año'] = self.feriados_df['fecha'].dt.dayofyear
            self.feriados_df['dia_semana'] = self.feriados_df['fecha'].dt.day_name()
            
            # Categorizar feriados
            self.feriados_df['categoria'] = self.feriados_df['descripcion'].apply(self._categorizar_feriado)
            
            # Crear diccionario rápido para búsquedas
            self.feriados_dict = {
                row['fecha'].date(): {
                    'descripcion': row['descripcion'],
                    'categoria': row['categoria']
                }
                for _, row in self.feriados_df.iterrows()
            }
            
            logger.info(f"Procesados {len(self.feriados_df)} feriados chilenos")
    
    def _categorizar_feriado(self, descripcion: str) -> str:
        """Categoriza los feriados según su tipo"""
        desc_lower = descripcion.lower()
        
        if any(word in desc_lower for word in ['navidad', 'año nuevo', 'santo', 'virgen', 'inmaculada', 'santos']):
            return 'Religioso'
        elif any(word in desc_lower for word in ['independencia', 'glorias', 'trabajo', 'patrias']):
            return 'Cívico'
        elif any(word in desc_lower for word in ['elecciones', 'plebiscito']):
            return 'Electoral'
        elif any(word in desc_lower for word in ['pueblos indígenas', 'evangélicas']):
            return 'Cultural'
        else:
            return 'Otro'
    
    def es_feriado(self, fecha: date) -> bool:
        """Verifica si una fecha es feriado en Chile"""
        return fecha in self.feriados_dict
    
    def obtener_feriado(self, fecha: date) -> Optional[Dict]:
        """Obtiene información del feriado para una fecha específica"""
        return self.feriados_dict.get(fecha)
    
    def marcar_feriados_en_dataframe(self, df: pd.DataFrame, columna_fecha: str = 'fecha') -> pd.DataFrame:
        """Marca los feriados en un DataFrame con datos de llamadas"""
        if columna_fecha not in df.columns:
            logger.warning(f"Columna {columna_fecha} no encontrada en el DataFrame")
            return df
        
        df_copy = df.copy()
        
        # Asegurar que la columna de fecha esté en formato datetime
        if not pd.api.types.is_datetime64_any_dtype(df_copy[columna_fecha]):
            df_copy[columna_fecha] = pd.to_datetime(df_copy[columna_fecha])
        
        # Crear columnas de análisis de feriados
        df_copy['fecha_solo'] = df_copy[columna_fecha].dt.date
        df_copy['es_feriado'] = df_copy['fecha_solo'].apply(self.es_feriado)
        
        # Obtener información detallada del feriado
        df_copy['feriado_info'] = df_copy['fecha_solo'].apply(self.obtener_feriado)
        df_copy['feriado_descripcion'] = df_copy['feriado_info'].apply(
            lambda x: x['descripcion'] if x else None
        )
        df_copy['feriado_categoria'] = df_copy['feriado_info'].apply(
            lambda x: x['categoria'] if x else 'Normal'
        )
        
        # Análisis de días alrededor de feriados
        df_copy['pre_feriado'] = df_copy['fecha_solo'].apply(self._es_pre_feriado)
        df_copy['post_feriado'] = df_copy['fecha_solo'].apply(self._es_post_feriado)
        df_copy['fin_de_semana_largo'] = df_copy.apply(self._es_fin_semana_largo, axis=1)
        
        # Crear etiqueta descriptiva para análisis
        df_copy['tipo_dia'] = df_copy.apply(self._determinar_tipo_dia, axis=1)
        
        return df_copy
    
    def _es_pre_feriado(self, fecha: date) -> bool:
        """Verifica si es el día anterior a un feriado"""
        siguiente_dia = fecha + timedelta(days=1)
        return self.es_feriado(siguiente_dia)
    
    def _es_post_feriado(self, fecha: date) -> bool:
        """Verifica si es el día posterior a un feriado"""
        dia_anterior = fecha - timedelta(days=1)
        return self.es_feriado(dia_anterior)
    
    def _es_fin_semana_largo(self, row) -> bool:
        """Determina si forma parte de un fin de semana largo"""
        fecha = row['fecha_solo']
        es_feriado = row['es_feriado']
        dia_semana = pd.to_datetime(fecha).dayofweek  # 0=Monday, 6=Sunday
        
        # Si es feriado y está cerca del fin de semana
        if es_feriado and (dia_semana == 4 or dia_semana == 0):  # Viernes o Lunes
            return True
        
        # Si es fin de semana y hay feriado adyacente
        if dia_semana >= 5:  # Sábado o Domingo
            for delta in [-1, 1]:
                fecha_check = fecha + timedelta(days=delta)
                if self.es_feriado(fecha_check):
                    return True
        
        return False
    
    def _determinar_tipo_dia(self, row) -> str:
        """Determina el tipo de día para análisis"""
        if row['es_feriado']:
            return f"Feriado ({row['feriado_categoria']})"
        elif row['fin_de_semana_largo']:
            return "Fin de Semana Largo"
        elif row['pre_feriado']:
            return "Pre-Feriado"
        elif row['post_feriado']:
            return "Post-Feriado"
        else:
            dia_semana = pd.to_datetime(row['fecha_solo']).dayofweek
            if dia_semana >= 5:
                return "Fin de Semana"
            else:
                return "Día Laboral"
    
    def analizar_patrones_feriados(self, df: pd.DataFrame) -> Dict:
        """Analiza patrones de llamadas en relación a feriados"""
        if 'es_feriado' not in df.columns:
            df = self.marcar_feriados_en_dataframe(df)
        
        # Análisis general
        total_registros = len(df)
        registros_feriados = len(df[df['es_feriado'] == True])
        registros_pre_feriado = len(df[df['pre_feriado'] == True])
        registros_post_feriado = len(df[df['post_feriado'] == True])
        
        # Análisis por tipo de día
        analisis_tipo_dia = df.groupby('tipo_dia').agg({
            df.columns[0]: 'count',  # Primera columna para contar registros
        }).rename(columns={df.columns[0]: 'cantidad_llamadas'})
        
        # Si hay columna de atención, analizarla
        if 'ATENDIDA' in df.columns:
            analisis_atencion = df.groupby(['tipo_dia', 'ATENDIDA']).size().unstack(fill_value=0)
            if 'Si' in analisis_atencion.columns and 'No' in analisis_atencion.columns:
                analisis_atencion['tasa_atencion'] = (
                    analisis_atencion['Si'] / (analisis_atencion['Si'] + analisis_atencion['No'])
                ) * 100
        else:
            analisis_atencion = None
        
        # Análisis por categoría de feriado
        if registros_feriados > 0:
            analisis_categorias = df[df['es_feriado'] == True].groupby('feriado_categoria').agg({
                df.columns[0]: 'count'
            }).rename(columns={df.columns[0]: 'cantidad_llamadas'})
        else:
            analisis_categorias = None
        
        # Análisis temporal (patrones horarios en feriados vs días normales)
        if 'hora' in df.columns:
            df['hora_num'] = pd.to_datetime(df['hora'], format='%H:%M:%S').dt.hour
            analisis_horario = df.groupby(['es_feriado', 'hora_num']).size().unstack(fill_value=0)
        else:
            analisis_horario = None
        
        return {
            'resumen': {
                'total_registros': total_registros,
                'registros_feriados': registros_feriados,
                'porcentaje_feriados': (registros_feriados / total_registros) * 100 if total_registros > 0 else 0,
                'registros_pre_feriado': registros_pre_feriado,
                'registros_post_feriado': registros_post_feriado
            },
            'por_tipo_dia': analisis_tipo_dia,
            'por_atencion': analisis_atencion,
            'por_categoria_feriado': analisis_categorias,
            'patrones_horarios': analisis_horario
        }
    
    def generar_calendario_visual(self, año: int = None) -> go.Figure:
        """Genera un calendario visual de feriados chilenos"""
        if año is None:
            año = datetime.now().year
        
        feriados_año = self.feriados_df[self.feriados_df['año'] == año]
        
        # Crear datos para el calendario
        fechas = pd.date_range(start=f'{año}-01-01', end=f'{año}-12-31', freq='D')
        calendario_data = []
        
        for fecha in fechas:
            es_feriado = fecha.date() in self.feriados_dict
            info_feriado = self.feriados_dict.get(fecha.date(), {})
            
            calendario_data.append({
                'fecha': fecha,
                'mes': fecha.month,
                'dia': fecha.day,
                'dia_semana': fecha.dayofweek,
                'es_feriado': es_feriado,
                'descripcion': info_feriado.get('descripcion', ''),
                'categoria': info_feriado.get('categoria', 'Normal')
            })
        
        df_calendario = pd.DataFrame(calendario_data)
        
        # Crear matriz para el heatmap
        semanas = []
        for mes in range(1, 13):
            datos_mes = df_calendario[df_calendario['mes'] == mes]
            primer_dia = datos_mes['fecha'].min()
            inicio_semana = primer_dia - timedelta(days=primer_dia.weekday())
            
            for semana in range(6):  # Máximo 6 semanas por mes
                semana_inicio = inicio_semana + timedelta(weeks=semana)
                semana_datos = datos_mes[
                    (datos_mes['fecha'] >= semana_inicio) & 
                    (datos_mes['fecha'] < semana_inicio + timedelta(days=7))
                ]
                
                if len(semana_datos) > 0:
                    semanas.append({
                        'mes': mes,
                        'semana': semana,
                        'feriados': semana_datos['es_feriado'].sum()
                    })
        
        # Crear figura
        fig = go.Figure()
        
        # Agregar scatter plot para feriados
        feriados_plot = df_calendario[df_calendario['es_feriado']]
        
        fig.add_trace(go.Scatter(
            x=feriados_plot['fecha'],
            y=[1] * len(feriados_plot),
            mode='markers',
            marker=dict(
                size=15,
                color=feriados_plot['categoria'].map({
                    'Religioso': '#FF6B6B',
                    'Cívico': '#4ECDC4',
                    'Electoral': '#45B7D1',
                    'Cultural': '#96CEB4',
                    'Otro': '#FFEAA7'
                }),
                symbol='square'
            ),
            text=feriados_plot['descripcion'],
            hovertemplate='<b>%{text}</b><br>Fecha: %{x}<extra></extra>',
            name='Feriados'
        ))
        
        fig.update_layout(
            title=f'Calendario de Feriados Chilenos {año}',
            xaxis_title='Fecha',
            yaxis=dict(showticklabels=False, showgrid=False),
            height=400,
            showlegend=True
        )
        
        return fig
    
    def obtener_metricas_feriados(self, df: pd.DataFrame) -> Dict:
        """Obtiene métricas específicas relacionadas con feriados"""
        if 'es_feriado' not in df.columns:
            df = self.marcar_feriados_en_dataframe(df)
        
        total_llamadas = len(df)
        llamadas_feriados = len(df[df['es_feriado']])
        llamadas_pre_feriado = len(df[df['pre_feriado']])
        llamadas_dias_normales = len(df[df['tipo_dia'] == 'Día Laboral'])
        
        # Calcular promedios
        promedio_normal = llamadas_dias_normales / max(len(df[df['tipo_dia'] == 'Día Laboral'].groupby('fecha_solo')), 1)
        promedio_feriado = llamadas_feriados / max(len(df[df['es_feriado']].groupby('fecha_solo')), 1)
        promedio_pre_feriado = llamadas_pre_feriado / max(len(df[df['pre_feriado']].groupby('fecha_solo')), 1)
        
        # Calcular variaciones
        variacion_feriado = ((promedio_feriado - promedio_normal) / promedio_normal * 100) if promedio_normal > 0 else 0
        variacion_pre_feriado = ((promedio_pre_feriado - promedio_normal) / promedio_normal * 100) if promedio_normal > 0 else 0
        
        return {
            'total_llamadas': total_llamadas,
            'llamadas_feriados': llamadas_feriados,
            'porcentaje_feriados': (llamadas_feriados / total_llamadas * 100) if total_llamadas > 0 else 0,
            'promedio_dia_normal': promedio_normal,
            'promedio_feriado': promedio_feriado,
            'promedio_pre_feriado': promedio_pre_feriado,
            'variacion_feriado_pct': variacion_feriado,
            'variacion_pre_feriado_pct': variacion_pre_feriado,
            'feriados_mas_activos': self._obtener_feriados_mas_activos(df)
        }
    
    def _obtener_feriados_mas_activos(self, df: pd.DataFrame) -> List[Dict]:
        """Obtiene los feriados con más actividad de llamadas"""
        if 'es_feriado' not in df.columns or 'feriado_descripcion' not in df.columns:
            return []
        
        feriados_activos = df[df['es_feriado'] == True].groupby(['fecha_solo', 'feriado_descripcion']).size().reset_index(name='llamadas')
        feriados_activos = feriados_activos.sort_values('llamadas', ascending=False).head(5)
        
        return feriados_activos.to_dict('records')

def mostrar_analisis_feriados_chilenos():
    """Interfaz de Streamlit para análisis de feriados chilenos"""
    
    st.header("🇨🇱 Análisis de Feriados Chilenos")
    st.markdown("### Impacto de feriados nacionales en patrones de llamadas")
    
    gestor = GestorFeriadosChilenos()
    
    # Mostrar información general de feriados
    with st.expander("📅 Calendario de Feriados Chilenos", expanded=False):
        año_seleccionado = st.selectbox("Seleccionar año", [2023, 2024, 2025], index=1)
        
        # Mostrar calendario visual
        fig_calendario = gestor.generar_calendario_visual(año_seleccionado)
        st.plotly_chart(fig_calendario, use_container_width=True)
        
        # Tabla de feriados del año
        feriados_año = gestor.feriados_df[gestor.feriados_df['año'] == año_seleccionado]
        st.dataframe(
            feriados_año[['fecha', 'descripcion', 'categoria', 'dia_semana']], 
            use_container_width=True
        )
    
    # Análisis de datos si están disponibles
    st.markdown("### 📊 Análisis de Impacto en Llamadas")
    
    # Verificar si hay datos cargados
    if hasattr(st.session_state, 'archivo_datos') and st.session_state.archivo_datos is not None:
        try:
            # Leer datos (esto debe ser adaptado según la estructura real de datos)
            df_sample = pd.DataFrame({
                'fecha': pd.date_range('2024-01-01', '2024-12-31', freq='D'),
                'llamadas': np.random.randint(50, 200, 365)
            })
            
            # Marcar feriados
            df_con_feriados = gestor.marcar_feriados_en_dataframe(df_sample, 'fecha')
            
            # Obtener métricas
            metricas = gestor.obtener_metricas_feriados(df_con_feriados)
            
            # Mostrar métricas principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Llamadas en Feriados",
                    f"{metricas['llamadas_feriados']:,}",
                    f"{metricas['porcentaje_feriados']:.1f}%"
                )
            
            with col2:
                st.metric(
                    "Promedio Día Normal",
                    f"{metricas['promedio_dia_normal']:.0f}",
                    "llamadas/día"
                )
            
            with col3:
                st.metric(
                    "Promedio Feriado",
                    f"{metricas['promedio_feriado']:.0f}",
                    f"{metricas['variacion_feriado_pct']:+.1f}%"
                )
            
            with col4:
                st.metric(
                    "Promedio Pre-Feriado",
                    f"{metricas['promedio_pre_feriado']:.0f}",
                    f"{metricas['variacion_pre_feriado_pct']:+.1f}%"
                )
            
            # Análisis detallado
            analisis = gestor.analizar_patrones_feriados(df_con_feriados)
            
            # Gráfico de patrones por tipo de día
            if analisis['por_tipo_dia'] is not None:
                st.subheader("📈 Patrones por Tipo de Día")
                
                fig_tipos = px.bar(
                    analisis['por_tipo_dia'].reset_index(),
                    x='tipo_dia',
                    y='cantidad_llamadas',
                    title='Distribución de Llamadas por Tipo de Día',
                    color='cantidad_llamadas',
                    color_continuous_scale='viridis'
                )
                
                fig_tipos.update_layout(
                    xaxis_title="Tipo de Día",
                    yaxis_title="Cantidad de Llamadas",
                    height=400
                )
                
                st.plotly_chart(fig_tipos, use_container_width=True)
            
            # Top feriados más activos
            if metricas['feriados_mas_activos']:
                st.subheader("🏆 Feriados con Mayor Actividad")
                
                df_top_feriados = pd.DataFrame(metricas['feriados_mas_activos'])
                if not df_top_feriados.empty:
                    fig_top = px.bar(
                        df_top_feriados,
                        x='feriado_descripcion',
                        y='llamadas',
                        title='Top 5 Feriados con Más Llamadas'
                    )
                    
                    fig_top.update_layout(
                        xaxis_title="Feriado",
                        yaxis_title="Cantidad de Llamadas",
                        height=400
                    )
                    
                    st.plotly_chart(fig_top, use_container_width=True)
            
            # Insights y recomendaciones
            st.subheader("💡 Insights y Recomendaciones")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"""
                **🔍 Análisis de Feriados:**
                
                • {metricas['porcentaje_feriados']:.1f}% de llamadas ocurren en feriados
                • Variación promedio en feriados: {metricas['variacion_feriado_pct']:+.1f}%
                • Días pre-feriado tienen {metricas['variacion_pre_feriado_pct']:+.1f}% de variación
                """)
            
            with col2:
                if metricas['variacion_feriado_pct'] > 10:
                    st.warning("⚠️ **Mayor demanda en feriados**: Considera reforzar personal")
                elif metricas['variacion_feriado_pct'] < -10:
                    st.success("✅ **Menor demanda en feriados**: Oportunidad para mantenimiento")
                else:
                    st.info("📊 **Demanda estable**: Patrón consistente en feriados")
        
        except Exception as e:
            st.error(f"Error en análisis de feriados: {e}")
            logger.error(f"Error en análisis de feriados: {e}")
    
    else:
        st.info("💡 Carga datos de llamadas para ver el análisis de impacto de feriados")
        
        # Mostrar ejemplo de análisis
        st.markdown("### 📋 Ejemplo de Análisis")
        
        st.markdown("""
        Cuando cargues tus datos, podrás ver:
        
        **📊 Métricas Principales:**
        - Volumen de llamadas en feriados vs días normales
        - Patrones de pre y post feriados
        - Tasas de atención por tipo de día
        
        **📈 Visualizaciones:**
        - Gráficos de distribución por tipo de día
        - Calendario visual de feriados
        - Top feriados con mayor actividad
        
        **💡 Insights Automáticos:**
        - Recomendaciones de staffing
        - Identificación de patrones estacionales
        - Planificación de recursos
        """)

# Función para integrar en el flujo principal
def integrar_feriados_en_analisis(df: pd.DataFrame, columna_fecha: str = 'fecha') -> pd.DataFrame:
    """Función utilitaria para integrar análisis de feriados en cualquier dataset"""
    gestor = GestorFeriadosChilenos()
    return gestor.marcar_feriados_en_dataframe(df, columna_fecha)

if __name__ == "__main__":
    # Para testing directo
    gestor = GestorFeriadosChilenos()
    print(f"Feriados cargados: {len(gestor.feriados_df)}")
    print("Algunos feriados 2024:")
    print(gestor.feriados_df[gestor.feriados_df['año'] == 2024][['fecha', 'descripcion']].head())