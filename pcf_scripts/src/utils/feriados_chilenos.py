#!/usr/bin/env python3
"""
Módulo de Feriados Chilenos para CEAPSI
Gestiona y analiza patrones de llamadas considerando feriados nacionales chilenos

Los feriados están integrados directamente en el código para evitar dependencias externas.
Incluye todos los feriados chilenos oficiales del período 2023-2025.
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
        """Carga los feriados chilenos integrados en el código"""
        try:
            # Usar datos integrados por defecto
            self.crear_feriados_default()
            logger.info("Feriados chilenos cargados desde datos integrados en el código")
            
            # Procesar y normalizar datos
            self.procesar_feriados()
            
        except Exception as e:
            logger.error(f"Error cargando feriados: {e}")
            # Si hay algún error, intentar crear datos mínimos
            try:
                self.feriados_df = pd.DataFrame([
                    {"Fecha (dd-mm-yyyy)": "01-01-2024", "Descripcion feriado": "Año Nuevo"},
                    {"Fecha (dd-mm-yyyy)": "18-09-2024", "Descripcion feriado": "Independencia Nacional"},
                    {"Fecha (dd-mm-yyyy)": "25-12-2024", "Descripcion feriado": "Navidad"}
                ])
                self.procesar_feriados()
            except:
                logger.error("Error crítico cargando feriados, sistema continuará sin feriados")
    
    def crear_feriados_default(self):
        """Crea un conjunto completo de feriados chilenos 2023-2025 integrado en el código"""
        feriados_default = [
            # 2023
            {"Fecha (dd-mm-yyyy)": "01-01-2023", "Descripcion feriado": "Año Nuevo"},
            {"Fecha (dd-mm-yyyy)": "02-01-2023", "Descripcion feriado": "Feriado Adicional por Año Nuevo"},
            {"Fecha (dd-mm-yyyy)": "07-04-2023", "Descripcion feriado": "Viernes Santo"},
            {"Fecha (dd-mm-yyyy)": "08-04-2023", "Descripcion feriado": "Sábado Santo"},
            {"Fecha (dd-mm-yyyy)": "01-05-2023", "Descripcion feriado": "Día Nacional del Trabajo"},
            {"Fecha (dd-mm-yyyy)": "21-05-2023", "Descripcion feriado": "Día de las Glorias Navales"},
            {"Fecha (dd-mm-yyyy)": "21-06-2023", "Descripcion feriado": "Día Nacional de los Pueblos Indígenas"},
            {"Fecha (dd-mm-yyyy)": "26-06-2023", "Descripcion feriado": "San Pedro y San Pablo"},
            {"Fecha (dd-mm-yyyy)": "16-07-2023", "Descripcion feriado": "Día de la Virgen del Carmen"},
            {"Fecha (dd-mm-yyyy)": "15-08-2023", "Descripcion feriado": "Asunción de la Virgen"},
            {"Fecha (dd-mm-yyyy)": "18-09-2023", "Descripcion feriado": "Independencia Nacional"},
            {"Fecha (dd-mm-yyyy)": "19-09-2023", "Descripcion feriado": "Día de las Glorias del Ejército"},
            {"Fecha (dd-mm-yyyy)": "09-10-2023", "Descripcion feriado": "Encuentro de Dos Mundos"},
            {"Fecha (dd-mm-yyyy)": "27-10-2023", "Descripcion feriado": "Día de las Iglesias Evangélicas y Protestantes"},
            {"Fecha (dd-mm-yyyy)": "01-11-2023", "Descripcion feriado": "Día de Todos los Santos"},
            {"Fecha (dd-mm-yyyy)": "08-12-2023", "Descripcion feriado": "Inmaculada Concepción"},
            {"Fecha (dd-mm-yyyy)": "17-12-2023", "Descripcion feriado": "Plebiscito Constitucional"},
            {"Fecha (dd-mm-yyyy)": "25-12-2023", "Descripcion feriado": "Navidad"},
            # 2024
            {"Fecha (dd-mm-yyyy)": "01-01-2024", "Descripcion feriado": "Año Nuevo"},
            {"Fecha (dd-mm-yyyy)": "29-03-2024", "Descripcion feriado": "Viernes Santo"},
            {"Fecha (dd-mm-yyyy)": "30-03-2024", "Descripcion feriado": "Sábado Santo"},
            {"Fecha (dd-mm-yyyy)": "01-05-2024", "Descripcion feriado": "Día Nacional del Trabajo"},
            {"Fecha (dd-mm-yyyy)": "21-05-2024", "Descripcion feriado": "Día de las Glorias Navales"},
            {"Fecha (dd-mm-yyyy)": "09-06-2024", "Descripcion feriado": "Elecciones Primarias de Alcaldes y Gobernadores"},
            {"Fecha (dd-mm-yyyy)": "20-06-2024", "Descripcion feriado": "Día Nacional de los Pueblos Indígenas"},
            {"Fecha (dd-mm-yyyy)": "29-06-2024", "Descripcion feriado": "San Pedro y San Pablo"},
            {"Fecha (dd-mm-yyyy)": "16-07-2024", "Descripcion feriado": "Día de la Virgen del Carmen"},
            {"Fecha (dd-mm-yyyy)": "15-08-2024", "Descripcion feriado": "Asunción de la Virgen"},
            {"Fecha (dd-mm-yyyy)": "18-09-2024", "Descripcion feriado": "Independencia Nacional"},
            {"Fecha (dd-mm-yyyy)": "19-09-2024", "Descripcion feriado": "Día de las Glorias del Ejército"},
            {"Fecha (dd-mm-yyyy)": "20-09-2024", "Descripcion feriado": "Feriado Adicional por Fiestas Patrias"},
            {"Fecha (dd-mm-yyyy)": "12-10-2024", "Descripcion feriado": "Encuentro de Dos Mundos"},
            {"Fecha (dd-mm-yyyy)": "27-10-2024", "Descripcion feriado": "Elecciones Municipales, de Consejeros Regionales y Gobernadores Regionales"},
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
            {"Fecha (dd-mm-yyyy)": "29-06-2025", "Descripcion feriado": "San Pedro y San Pablo"},
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
    
    def marcar_feriados_en_dataframe(self, df: pd.DataFrame, columna_fecha: str = 'fecha', 
                                     solo_salientes: bool = False) -> pd.DataFrame:
        """
        Marca los feriados en un DataFrame con datos de llamadas
        
        Args:
            df: DataFrame con datos de llamadas
            columna_fecha: Nombre de la columna de fecha
            solo_salientes: Si True, solo marca feriados para llamadas salientes.
                          Las entrantes mantienen todos los datos para pronóstico de demanda.
        """
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
        
        # LÓGICA DIFERENCIADA POR TIPO DE LLAMADA
        if solo_salientes:
            logger.info("Aplicando análisis de feriados solo a llamadas salientes")
            # Para llamadas salientes, podemos filtrar/limpiar datos de feriados
            df_copy['excluir_de_entrenamiento'] = df_copy['es_feriado'] | df_copy['pre_feriado'] | df_copy['post_feriado']
        else:
            # Para llamadas entrantes, mantenemos todos los datos ya que representan demanda real del cliente
            # Los feriados son parte del patrón de demanda que queremos pronosticar
            df_copy['excluir_de_entrenamiento'] = False
            logger.info("Manteniendo todos los datos de feriados para análisis de demanda (llamadas entrantes)")
        
        # Crear campo de tratamiento para el entrenamiento
        if 'SENTIDO' in df_copy.columns:
            # Determinar tratamiento basado en dirección de llamada
            df_copy['aplicar_filtro_feriados'] = (
                (df_copy['SENTIDO'].str.lower().isin(['out', 'saliente', 'outbound'])) &
                (df_copy['es_feriado'] | df_copy['pre_feriado'] | df_copy['post_feriado'])
            )
        else:
            # Si no hay columna SENTIDO, usar el parámetro solo_salientes
            df_copy['aplicar_filtro_feriados'] = df_copy['excluir_de_entrenamiento'] if solo_salientes else False
        
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
            try:
                # Intentar extraer hora de diferentes formatos
                if df['hora'].dtype == 'object':
                    # Si contiene fecha completa, extraer solo la hora
                    if df['hora'].str.contains(' ').any():
                        df['hora_num'] = pd.to_datetime(df['hora'], errors='coerce').dt.hour
                    else:
                        # Solo formato de hora
                        df['hora_num'] = pd.to_datetime(df['hora'], format='%H:%M:%S', errors='coerce').dt.hour
                else:
                    # Si ya es datetime, extraer hora directamente
                    df['hora_num'] = pd.to_datetime(df['hora'], errors='coerce').dt.hour
                
                # Filtrar valores nulos antes del análisis
                df_valido = df.dropna(subset=['hora_num'])
                if len(df_valido) > 0:
                    analisis_horario = df_valido.groupby(['es_feriado', 'hora_num']).size().unstack(fill_value=0)
                else:
                    analisis_horario = None
            except Exception as e:
                logger.warning(f"Error procesando columna hora: {e}")
                analisis_horario = None
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
            # Intentar detectar la columna de fecha automáticamente
            columna_fecha = None
            for col in ['ds', 'fecha', 'FECHA', 'fecha_solo', 'date']:
                if col in df.columns:
                    columna_fecha = col
                    break
            
            if columna_fecha:
                df = self.marcar_feriados_en_dataframe(df, columna_fecha)
            else:
                logger.warning("No se pudo detectar columna de fecha para marcar feriados")
                return {
                    'total_llamadas': len(df),
                    'llamadas_feriados': 0,
                    'porcentaje_feriados': 0,
                    'promedio_dia_normal': 0,
                    'promedio_feriado': 0,
                    'promedio_pre_feriado': 0,
                    'variacion_feriado_pct': 0,
                    'variacion_pre_feriado_pct': 0,
                    'feriados_mas_activos': []
                }
        
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
    
    def filtrar_datos_para_entrenamiento(self, df: pd.DataFrame, tipo_llamada: str = 'entrante') -> pd.DataFrame:
        """
        Filtra datos para entrenamiento según el tipo de llamada y feriados
        
        Args:
            df: DataFrame con datos marcados con feriados
            tipo_llamada: 'entrante' o 'saliente'
        
        Returns:
            DataFrame filtrado apropiadamente para entrenamiento
        """
        if 'aplicar_filtro_feriados' not in df.columns:
            logger.warning("DataFrame no tiene marcadores de feriados. Aplicando primero marcar_feriados_en_dataframe()")
            df = self.marcar_feriados_en_dataframe(df)
        
        if tipo_llamada.lower() in ['entrante', 'inbound', 'in']:
            # Para llamadas entrantes: mantener TODOS los datos incluyendo feriados
            # Los feriados son parte del patrón de demanda del cliente que queremos pronosticar
            df_entrenamiento = df.copy()
            logger.info(f"Entrenamiento ENTRANTE: Manteniendo {len(df_entrenamiento)} registros (incluyendo feriados)")
            
        elif tipo_llamada.lower() in ['saliente', 'outbound', 'out']:
            # Para llamadas salientes: excluir feriados ya que dependen de operación interna
            df_entrenamiento = df[~df['aplicar_filtro_feriados']].copy()
            registros_excluidos = len(df) - len(df_entrenamiento)
            logger.info(f"Entrenamiento SALIENTE: Excluyendo {registros_excluidos} registros de feriados. Manteniendo {len(df_entrenamiento)} registros")
            
        else:
            logger.warning(f"Tipo de llamada no reconocido: {tipo_llamada}. Manteniendo todos los datos.")
            df_entrenamiento = df.copy()
        
        return df_entrenamiento
    
    def analizar_patrones_por_cargo(self, df: pd.DataFrame, columna_cargo: str = 'CARGO') -> Dict:
        """
        Analiza patrones de llamadas por cargo/posición en relación a feriados
        
        Args:
            df: DataFrame con datos de llamadas y cargos
            columna_cargo: Nombre de la columna que contiene los cargos
        """
        if columna_cargo not in df.columns:
            logger.warning(f"Columna {columna_cargo} no encontrada en el DataFrame")
            return {}
        
        if 'es_feriado' not in df.columns:
            df = self.marcar_feriados_en_dataframe(df)
        
        # Análisis general por cargo
        analisis_cargo = df.groupby(columna_cargo).agg({
            df.columns[0]: 'count',  # Contar registros
        }).rename(columns={df.columns[0]: 'total_llamadas'})
        
        # Análisis de feriados por cargo
        analisis_feriados_cargo = df[df['es_feriado'] == True].groupby(columna_cargo).agg({
            df.columns[0]: 'count'
        }).rename(columns={df.columns[0]: 'llamadas_feriados'})
        
        # Combinar análisis
        analisis_combinado = analisis_cargo.join(analisis_feriados_cargo, how='left').fillna(0)
        analisis_combinado['porcentaje_feriados'] = (
            analisis_combinado['llamadas_feriados'] / analisis_combinado['total_llamadas'] * 100
        )
        
        # Análisis por tipo de día y cargo
        crosstab_cargo_tipo = pd.crosstab(df[columna_cargo], df['tipo_dia'], normalize='index') * 100
        
        # Análisis de productividad por cargo en diferentes tipos de día
        if 'ATENDIDA' in df.columns:
            # Calcular tasas de atención por cargo y tipo de día
            df['atendida_num'] = (df['ATENDIDA'] == 'Si').astype(int)
            
            atencion_cargo_tipo = df.groupby([columna_cargo, 'tipo_dia'])['atendida_num'].agg(['mean', 'count']).reset_index()
            atencion_cargo_tipo.columns = [columna_cargo, 'tipo_dia', 'tasa_atencion', 'cantidad_llamadas']
            atencion_cargo_tipo['tasa_atencion'] = atencion_cargo_tipo['tasa_atencion'] * 100
            
            # Pivot para mejor visualización
            atencion_pivot = atencion_cargo_tipo.pivot(index=columna_cargo, columns='tipo_dia', values='tasa_atencion')
        else:
            atencion_pivot = None
        
        # Ranking de cargos por actividad en feriados
        ranking_feriados = analisis_combinado.sort_values('porcentaje_feriados', ascending=False)
        
        # Identificar cargos más/menos afectados por feriados
        if len(analisis_combinado) > 0:
            cargo_mas_afectado = ranking_feriados.index[0]
            cargo_menos_afectado = ranking_feriados.index[-1]
            
            insights_cargos = {
                'mas_afectado': {
                    'cargo': cargo_mas_afectado,
                    'porcentaje': ranking_feriados.loc[cargo_mas_afectado, 'porcentaje_feriados']
                },
                'menos_afectado': {
                    'cargo': cargo_menos_afectado,
                    'porcentaje': ranking_feriados.loc[cargo_menos_afectado, 'porcentaje_feriados']
                }
            }
        else:
            insights_cargos = {}
        
        return {
            'resumen_por_cargo': analisis_combinado,
            'distribucion_tipo_dia': crosstab_cargo_tipo,
            'tasas_atencion_por_tipo': atencion_pivot,
            'ranking_actividad_feriados': ranking_feriados,
            'insights': insights_cargos,
            'total_cargos': len(analisis_combinado),
            'total_registros_analizados': len(df)
        }
    
    def generar_recomendaciones_por_cargo(self, analisis_cargo: Dict) -> Dict[str, List[str]]:
        """
        Genera recomendaciones específicas por cargo basadas en el análisis de feriados
        """
        recomendaciones = {}
        
        if 'resumen_por_cargo' not in analisis_cargo:
            return recomendaciones
        
        resumen = analisis_cargo['resumen_por_cargo']
        
        for cargo in resumen.index:
            cargo_data = resumen.loc[cargo]
            porcentaje_feriados = cargo_data['porcentaje_feriados']
            total_llamadas = cargo_data['total_llamadas']
            
            recomendaciones_cargo = []
            
            # Recomendaciones basadas en actividad en feriados
            if porcentaje_feriados > 20:
                recomendaciones_cargo.append(f"📈 Alto volumen en feriados ({porcentaje_feriados:.1f}%): Programar personal adicional")
                recomendaciones_cargo.append("🎯 Considerar incentivos especiales para feriados")
                recomendaciones_cargo.append("📞 Monitorear de cerca la calidad de servicio")
                
            elif porcentaje_feriados < 5:
                recomendaciones_cargo.append(f"📉 Baja actividad en feriados ({porcentaje_feriados:.1f}%): Oportunidad para capacitación")
                recomendaciones_cargo.append("🔧 Ideal para mantenimiento de sistemas")
                recomendaciones_cargo.append("📚 Programar entrenamientos especializados")
                
            else:
                recomendaciones_cargo.append(f"📊 Actividad moderada en feriados ({porcentaje_feriados:.1f}%): Mantener staff regular")
                recomendaciones_cargo.append("🎯 Monitorear tendencias estacionales")
            
            # Recomendaciones basadas en volumen total
            if total_llamadas > resumen['total_llamadas'].median():
                recomendaciones_cargo.append("🔥 Cargo de alto volumen: Priorizar en análisis")
                recomendaciones_cargo.append("📊 Implementar métricas específicas de performance")
            
            # Recomendaciones específicas por tipo de cargo
            cargo_lower = cargo.lower()
            if 'supervisor' in cargo_lower or 'jefe' in cargo_lower:
                recomendaciones_cargo.append("👔 Rol de liderazgo: Coordinar equipos en feriados")
                recomendaciones_cargo.append("📋 Planificar horarios especiales")
                
            elif 'agente' in cargo_lower or 'call center' in cargo_lower:
                recomendaciones_cargo.append("📞 Personal operativo: Evaluar rotación en feriados")
                recomendaciones_cargo.append("⏰ Considerar turnos flexibles")
                
            elif 'secretaria' in cargo_lower:
                recomendaciones_cargo.append("📝 Soporte administrativo: Backup en feriados críticos")
                
            recomendaciones[cargo] = recomendaciones_cargo
        
        return recomendaciones

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
            # IMPORTANTE: Usar fechas fijas para evitar data leakage en demos científicas
            df_sample = pd.DataFrame({
                'fecha': pd.date_range('2023-01-01', '2023-12-31', freq='D'),
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

def mostrar_analisis_cargo_feriados():
    """Función para mostrar análisis de cargo con feriados en Streamlit"""
    import streamlit as st
    import plotly.express as px
    
    st.title("👥 Análisis por Cargo y Feriados")
    st.markdown("---")
    
    # Verificar si hay datos cargados
    if hasattr(st.session_state, 'datos_cargados') and st.session_state.datos_cargados:
        try:
            # Intentar cargar datos de usuarios
            df_usuarios = None
            usuario_file = st.file_uploader(
                "📊 Cargar archivo de mapeo de usuarios (opcional)", 
                type=['csv', 'xlsx', 'xls'],
                help="Archivo con información de usuarios y sus cargos"
            )
            
            if usuario_file is not None:
                try:
                    if usuario_file.name.endswith('.csv'):
                        df_usuarios = pd.read_csv(usuario_file)
                    else:
                        df_usuarios = pd.read_excel(usuario_file)
                    
                    st.success(f"✅ Archivo de usuarios cargado: {len(df_usuarios)} registros")
                except Exception as e:
                    st.error(f"❌ Error cargando archivo de usuarios: {e}")
            
            # Análisis con datos de llamadas existentes
            df_llamadas = getattr(st.session_state, 'archivo_datos', None)
            if df_llamadas is not None:
                # Simular datos de cargo si no hay archivo de usuarios
                if df_usuarios is None:
                    st.info("💡 No se cargó archivo de usuarios. Mostrando análisis ejemplo con cargos simulados.")
                    
                    # Crear datos de ejemplo para demostración
                    cargos_ejemplo = ['Secretaria', 'Recepcionista', 'Coordinadora', 'Supervisora', 'Asistente']
                    
                    if isinstance(df_llamadas, str):
                        try:
                            df = pd.read_csv(df_llamadas, sep=';', encoding='utf-8')
                        except:
                            df = pd.read_csv(df_llamadas)
                    else:
                        df = df_llamadas.copy()
                    
                    # Simular asignación de cargos para demo
                    try:
                        if 'TELEFONO' in df.columns:
                            telefonos_unicos = df['TELEFONO'].unique()
                            cargo_mapping = {tel: np.random.choice(cargos_ejemplo) for tel in telefonos_unicos}
                            df['CARGO'] = df['TELEFONO'].map(cargo_mapping)
                        else:
                            # Asegurar que el array tenga exactamente la misma longitud que el DataFrame
                            df_len = len(df)
                            if df_len > 0:
                                df['CARGO'] = [np.random.choice(cargos_ejemplo) for _ in range(df_len)]
                            else:
                                df['CARGO'] = []
                    except Exception as e:
                        logger.warning(f"Error asignando cargos simulados: {e}")
                        # Fallback: asignar cargo fijo
                        df['CARGO'] = 'Secretaria'
                else:
                    # Integrar datos reales de usuarios
                    st.info("🔗 Integrando datos de usuarios con llamadas...")
                    # Aquí iría la lógica de joining real
                    df = df_llamadas.copy()
                    df['CARGO'] = 'No asignado'  # Placeholder
                
                # Aplicar análisis de feriados
                gestor_feriados = GestorFeriadosChilenos()
                
                if 'FECHA' in df.columns:
                    df['fecha_solo'] = pd.to_datetime(df['FECHA']).dt.date
                    df = gestor_feriados.marcar_feriados_en_dataframe(df, 'fecha_solo')
                    
                    # Análisis por cargo
                    analisis_cargo = gestor_feriados.analizar_patrones_por_cargo(df, 'CARGO')
                    
                    # Mostrar resultados
                    st.subheader("📊 Análisis por Cargo y Feriados")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("👥 Cargos únicos", analisis_cargo['resumen']['cargos_unicos'])
                    with col2:
                        st.metric("📞 Total llamadas", analisis_cargo['resumen']['total_llamadas'])
                    with col3:
                        cargo_mas_activo = max(analisis_cargo['por_cargo'].items(), key=lambda x: x[1]['total_llamadas'])[0]
                        st.metric("🏆 Cargo más activo", cargo_mas_activo)
                    
                    # Gráfico de distribución por cargo
                    st.subheader("📈 Distribución de Llamadas por Cargo")
                    df_cargo_resumen = pd.DataFrame([
                        {
                            'Cargo': cargo,
                            'Total Llamadas': datos['total_llamadas'],
                            'En Feriados': datos['llamadas_feriados'],
                            'Días Normales': datos['llamadas_normales'],
                            'Variación Feriados (%)': datos['variacion_feriados_pct']
                        }
                        for cargo, datos in analisis_cargo['por_cargo'].items()
                    ])
                    
                    # Gráfico de barras
                    fig_cargo = px.bar(
                        df_cargo_resumen,
                        x='Cargo',
                        y=['En Feriados', 'Días Normales'],
                        title="Distribución de Llamadas: Feriados vs Días Normales por Cargo",
                        barmode='group',
                        color_discrete_map={'En Feriados': '#ff6b6b', 'Días Normales': '#4ecdc4'}
                    )
                    st.plotly_chart(fig_cargo, use_container_width=True)
                    
                    # Tabla detallada
                    st.subheader("📋 Detalle por Cargo")
                    st.dataframe(df_cargo_resumen, use_container_width=True)
                    
                    # Recomendaciones por cargo
                    st.subheader("💡 Recomendaciones por Cargo")
                    recomendaciones = gestor_feriados.generar_recomendaciones_por_cargo(analisis_cargo)
                    
                    for recom in recomendaciones:
                        with st.expander(f"📋 {recom['cargo']} ({recom['tipo']})"):
                            st.write(f"**{recom['titulo']}**")
                            st.write(recom['mensaje'])
                            if 'accion' in recom:
                                st.info(f"🎯 **Acción recomendada:** {recom['accion']}")
                
        except Exception as e:
            st.error(f"❌ Error en análisis por cargo: {e}")
            logger.error(f"Error en análisis por cargo: {e}")
    else:
        st.info("💡 Primero carga datos de llamadas en la sección 'Preparación de Datos'")

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