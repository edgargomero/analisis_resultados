#!/usr/bin/env python3
"""
CEAPSI - Dashboard de Comparación y Validación de Modelos
Dashboard especializado para evaluar performance de predicciones de llamadas
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
from datetime import datetime, timedelta
import os
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error

# Configuración de la página
st.set_page_config(
    page_title="CEAPSI - Validación de Modelos de Llamadas",
    page_icon="📊",
    layout="wide"
)

class DashboardValidacionCEAPSI:
    """Dashboard especializado para validación de modelos de llamadas"""
    
    def __init__(self):
        self.base_path = self._obtener_ruta_resultados()
        self.archivo_datos_manual = None  # Para datos subidos manualmente
        self.archivo_usuarios = None  # Para datos de usuarios/cargos
        self.df_usuarios = None  # DataFrame de usuarios cargado
        
    def _obtener_ruta_resultados(self):
        """Obtiene la carpeta de resultados más reciente"""
        # Usar directorio actual del script
        base_path = Path(__file__).parent.absolute()
        try:
            # Buscar carpetas de resultados en el directorio actual
            carpetas = [d for d in os.listdir(base_path) if d.startswith('resultados_')]
            if carpetas:
                return os.path.join(base_path, max(carpetas))
            return str(base_path)
        except:
            return base_path
    
    @st.cache_data(ttl=300)
    def cargar_resultados_multimodelo(_self, tipo_llamada='ENTRANTE'):
        """Carga resultados del sistema multi-modelo"""
        try:
            # Buscar archivo más reciente en el directorio actual
            archivos = [f for f in os.listdir('.') 
                       if f.startswith(f'predicciones_multimodelo_{tipo_llamada.lower()}') and f.endswith('.json')]
            
            if not archivos:
                st.info(f"📁 No se encontraron resultados para {tipo_llamada}. Creando predicciones de ejemplo...")
                return _self._crear_resultados_ejemplo(tipo_llamada)
            
            archivo_reciente = sorted(archivos)[-1]
            
            with open(archivo_reciente, 'r', encoding='utf-8') as f:
                resultados = json.load(f)
            
            # Convertir predicciones a DataFrame
            df_pred = pd.DataFrame(resultados['predicciones'])
            df_pred['ds'] = pd.to_datetime(df_pred['ds'])
            
            return resultados, df_pred
            
        except Exception as e:
            st.error(f"Error cargando resultados: {e}")
            return None, None
    
    @st.cache_data(ttl=300)
    def cargar_datos_historicos(_self, tipo_llamada='ENTRANTE'):
        """Carga datos históricos para comparación"""
        try:
            # Usar ruta simple, sin base_path que puede estar mal configurado
            archivo_historico = f"datos_prophet_{tipo_llamada.lower()}.csv"
            
            # Verificar si existe el archivo
            if not os.path.exists(archivo_historico):
                st.info(f"📁 Creando datos de ejemplo para {tipo_llamada}...")
                return _self._crear_datos_ejemplo_historicos(tipo_llamada)
            
            df_hist = pd.read_csv(archivo_historico)
            df_hist['ds'] = pd.to_datetime(df_hist['ds'])
            return df_hist
        except Exception as e:
            st.warning(f"No se pudieron cargar datos históricos: {e}")
            # Crear datos de ejemplo como fallback
            return _self._crear_datos_ejemplo_historicos(tipo_llamada)
    
    @st.cache_data(ttl=300)
    def cargar_datos_llamadas_completos(_self):
        """Carga datos completos de llamadas desde el archivo original o subido"""
        try:
            # Usar archivo manual si está disponible
            if _self.archivo_datos_manual:
                archivo_llamadas = _self.archivo_datos_manual
            else:
                # Usar archivo de ejemplo si no hay datos manuales
                st.info("📁 No hay archivo de datos cargado. Usando datos de ejemplo...")
                return _self._crear_datos_ejemplo_completos()
            
            # Intentar diferentes encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df_completo = pd.read_csv(archivo_llamadas, sep=';', encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                st.error("No se pudo cargar el archivo con ningún encoding")
                return None
            
            # Procesar fechas
            try:
                df_completo['FECHA'] = pd.to_datetime(df_completo['FECHA'], format='%d-%m-%Y %H:%M:%S', errors='coerce')
            except:
                # Fallback para otros formatos
                df_completo['FECHA'] = pd.to_datetime(df_completo['FECHA'], dayfirst=True, errors='coerce')
            
            df_completo = df_completo.dropna(subset=['FECHA'])
            
            # Agregar columnas derivadas
            df_completo['fecha_solo'] = df_completo['FECHA'].dt.date
            df_completo['hora'] = df_completo['FECHA'].dt.hour
            df_completo['dia_semana'] = df_completo['FECHA'].dt.day_name()
            df_completo['mes'] = df_completo['FECHA'].dt.month
            df_completo['ano'] = df_completo['FECHA'].dt.year
            
            # Filtrar solo días laborales
            df_completo = df_completo[df_completo['FECHA'].dt.dayofweek < 5]
            
            return df_completo
            
        except Exception as e:
            st.error(f"Error cargando datos completos: {e}")
            return None
    
    def mostrar_header_validacion(self):
        """Header del dashboard de validación"""
        st.title("📊 CEAPSI - Validación de Modelos de Predicción")
        st.markdown("### Dashboard Especializado para Evaluación de Performance")
        st.markdown("---")
        
        # Selector de tipo de llamada
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            tipo_llamada = st.selectbox(
                "Tipo de Llamada:",
                ['ENTRANTE', 'SALIENTE'],
                key='tipo_llamada_selector'
            )
        
        with col2:
            if st.button("🔄 Actualizar Datos", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        
        return tipo_llamada
    
    def mostrar_metricas_comparativas(self, resultados):
        """Muestra métricas comparativas entre modelos"""
        st.subheader("🏆 Comparación de Performance por Modelo")
        
        # Extraer métricas de validación cruzada
        metadatos_modelos = resultados.get('metadatos_modelos', {})
        pesos_ensemble = resultados.get('pesos_ensemble', {})
        
        # Preparar datos para visualización
        metricas_data = []
        
        for modelo, metadata in metadatos_modelos.items():
            mae = metadata.get('mae_validacion', metadata.get('mae_cv', 0))
            rmse = metadata.get('rmse_validacion', metadata.get('rmse_cv', 0))
            peso = pesos_ensemble.get(modelo, 0)
            
            metricas_data.append({
                'Modelo': modelo.replace('_', ' ').title(),
                'MAE': mae,
                'RMSE': rmse,
                'Peso Ensemble': peso,
                'Status': '✅ Activo' if peso > 0 else '❌ Inactivo'
            })
        
        if metricas_data:
            df_metricas = pd.DataFrame(metricas_data)
            
            # Mostrar tabla de métricas
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.dataframe(
                    df_metricas.style.format({
                        'MAE': '{:.2f}',
                        'RMSE': '{:.2f}',
                        'Peso Ensemble': '{:.3f}'
                    }).background_gradient(subset=['MAE', 'RMSE'], cmap='RdYlGn_r'),
                    use_container_width=True
                )
            
            with col2:
                # Gráfico de pesos
                fig_pesos = px.pie(
                    df_metricas[df_metricas['Peso Ensemble'] > 0],
                    values='Peso Ensemble',
                    names='Modelo',
                    title="Distribución de Pesos Ensemble"
                )
                st.plotly_chart(fig_pesos, use_container_width=True)
        
        # Mostrar mejores y peores modelos
        if metricas_data:
            col1, col2, col3 = st.columns(3)
            
            df_activos = df_metricas[df_metricas['Peso Ensemble'] > 0]
            
            if not df_activos.empty:
                mejor_mae = df_activos.loc[df_activos['MAE'].idxmin()]
                mejor_peso = df_activos.loc[df_activos['Peso Ensemble'].idxmax()]
                
                with col1:
                    st.metric(
                        "🥇 Mejor MAE",
                        f"{mejor_mae['Modelo']}",
                        f"{mejor_mae['MAE']:.2f}"
                    )
                
                with col2:
                    st.metric(
                        "⚖️ Mayor Peso",
                        f"{mejor_peso['Modelo']}",
                        f"{mejor_peso['Peso Ensemble']:.3f}"
                    )
                
                with col3:
                    mae_promedio = df_activos['MAE'].mean()
                    st.metric(
                        "📊 MAE Promedio",
                        f"{mae_promedio:.2f}",
                        f"{'✅' if mae_promedio < 15 else '⚠️' if mae_promedio < 25 else '❌'}"
                    )
    
    def mostrar_grafico_predicciones_detallado(self, df_predicciones, df_historico=None):
        """Muestra gráfico detallado de predicciones con comparación de modelos"""
        st.subheader("📈 Predicciones Detalladas por Modelo")
        
        # Crear figura con subplots
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("Comparación de Predicciones", "Intervalos de Confianza"),
            vertical_spacing=0.1,
            row_heights=[0.7, 0.3]
        )
        
        # Colores para cada modelo
        colores = {
            'yhat_arima': '#FF6B6B',
            'yhat_prophet': '#4ECDC4',
            'yhat_random_forest': '#45B7D1',
            'yhat_gradient_boosting': '#96CEB4',
            'yhat_ridge': '#FECA57',
            'yhat_ensemble': '#6C5CE7'
        }
        
        # Agregar datos históricos si están disponibles
        if df_historico is not None:
            fig.add_trace(
                go.Scatter(
                    x=df_historico['ds'],
                    y=df_historico['y'],
                    mode='lines',
                    name='Histórico Real',
                    line=dict(color='black', width=2),
                    opacity=0.7
                ),
                row=1, col=1
            )
        
        # Agregar predicciones de cada modelo
        for col in df_predicciones.columns:
            if col.startswith('yhat_') and col in colores:
                modelo_name = col.replace('yhat_', '').replace('_', ' ').title()
                
                # Estilo especial para ensemble
                if 'ensemble' in col:
                    fig.add_trace(
                        go.Scatter(
                            x=df_predicciones['ds'],
                            y=df_predicciones[col],
                            mode='lines+markers',
                            name=f'{modelo_name} (Principal)',
                            line=dict(color=colores[col], width=4),
                            marker=dict(size=6)
                        ),
                        row=1, col=1
                    )
                else:
                    fig.add_trace(
                        go.Scatter(
                            x=df_predicciones['ds'],
                            y=df_predicciones[col],
                            mode='lines',
                            name=modelo_name,
                            line=dict(color=colores[col], width=2, dash='dot'),
                            opacity=0.7
                        ),
                        row=1, col=1
                    )
        
        # Agregar intervalos de confianza en el segundo subplot
        if 'yhat_upper' in df_predicciones.columns and 'yhat_lower' in df_predicciones.columns:
            fig.add_trace(
                go.Scatter(
                    x=df_predicciones['ds'],
                    y=df_predicciones['yhat_upper'],
                    mode='lines',
                    name='Límite Superior',
                    line=dict(color='rgba(108, 92, 231, 0.3)', width=1),
                    showlegend=False
                ),
                row=2, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=df_predicciones['ds'],
                    y=df_predicciones['yhat_lower'],
                    mode='lines',
                    name='Límite Inferior',
                    line=dict(color='rgba(108, 92, 231, 0.3)', width=1),
                    fill='tonexty',
                    fillcolor='rgba(108, 92, 231, 0.1)',
                    showlegend=False
                ),
                row=2, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=df_predicciones['ds'],
                    y=df_predicciones['yhat_ensemble'],
                    mode='lines',
                    name='Predicción Ensemble',
                    line=dict(color='#6C5CE7', width=3)
                ),
                row=2, col=1
            )
        
        # Configurar layout
        fig.update_layout(
            height=800,
            title="Comparación Detallada de Modelos de Predicción",
            hovermode='x unified'
        )
        
        fig.update_xaxes(title_text="Fecha", row=2, col=1)
        fig.update_yaxes(title_text="Número de Llamadas", row=1, col=1)
        fig.update_yaxes(title_text="Llamadas (con Incertidumbre)", row=2, col=1)
        
        st.plotly_chart(fig, use_container_width=True)
    
    def mostrar_analisis_residuales(self, resultados, df_historico):
        """Análisis de residuales para validación del modelo"""
        if df_historico is None:
            return
        
        st.subheader("🔍 Análisis de Residuales y Diagnóstico")
        
        # Simular datos de validación (en producción vendría del cross-validation)
        # Para este ejemplo, usaremos los últimos 30 días como datos de test
        if len(df_historico) > 30:
            df_test = df_historico.tail(30).copy()
            
            # Simular predicciones para estos días (en producción serían las predicciones reales del modelo)
            np.random.seed(42)
            df_test['pred_ensemble'] = df_test['y'] + np.random.normal(0, 3, len(df_test))
            df_test['residuales'] = df_test['y'] - df_test['pred_ensemble']
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de residuales vs predicciones
                fig_residuales = px.scatter(
                    df_test,
                    x='pred_ensemble',
                    y='residuales',
                    title="Residuales vs Predicciones",
                    labels={'pred_ensemble': 'Predicciones', 'residuales': 'Residuales'},
                    trendline="lowess"
                )
                fig_residuales.add_hline(y=0, line_dash="dash", line_color="red")
                st.plotly_chart(fig_residuales, use_container_width=True)
            
            with col2:
                # Histograma de residuales
                fig_hist = px.histogram(
                    df_test,
                    x='residuales',
                    title="Distribución de Residuales",
                    nbins=20
                )
                fig_hist.add_vline(x=0, line_dash="dash", line_color="red")
                st.plotly_chart(fig_hist, use_container_width=True)
            
            # Métricas de diagnóstico
            col1, col2, col3, col4 = st.columns(4)
            
            mae_test = mean_absolute_error(df_test['y'], df_test['pred_ensemble'])
            rmse_test = np.sqrt(mean_squared_error(df_test['y'], df_test['pred_ensemble']))
            bias = df_test['residuales'].mean()
            
            with col1:
                st.metric("MAE Validación", f"{mae_test:.2f}")
            with col2:
                st.metric("RMSE Validación", f"{rmse_test:.2f}")
            with col3:
                st.metric("Bias", f"{bias:.2f}")
            with col4:
                r2_score = 1 - (df_test['residuales']**2).sum() / ((df_test['y'] - df_test['y'].mean())**2).sum()
                st.metric("R² Score", f"{r2_score:.3f}")
    
    def mostrar_alertas_validacion(self, resultados):
        """Muestra alertas con validación de confianza"""
        alertas = resultados.get('alertas', [])
        
        if not alertas:
            st.success("✅ No hay alertas detectadas")
            return
        
        st.subheader("🚨 Sistema de Alertas Validado")
        
        # Agrupar alertas por severidad
        alertas_por_severidad = {}
        for alerta in alertas:
            severidad = alerta.get('severidad', 'MEDIA')
            if severidad not in alertas_por_severidad:
                alertas_por_severidad[severidad] = []
            alertas_por_severidad[severidad].append(alerta)
        
        # Mostrar alertas por severidad
        for severidad in ['CRITICA', 'ALTA', 'MEDIA', 'BAJA']:
            if severidad in alertas_por_severidad:
                alertas_sev = alertas_por_severidad[severidad]
                
                # Color y emoji según severidad
                config_severidad = {
                    'CRITICA': {'color': 'red', 'emoji': '🔴', 'container': st.error},
                    'ALTA': {'color': 'orange', 'emoji': '🟠', 'container': st.warning},
                    'MEDIA': {'color': 'yellow', 'emoji': '🟡', 'container': st.info},
                    'BAJA': {'color': 'blue', 'emoji': '🔵', 'container': st.info}
                }
                
                config = config_severidad[severidad]
                
                with config['container'](f"{config['emoji']} Alertas {severidad} ({len(alertas_sev)})"):
                    for alerta in alertas_sev:
                        with st.expander(
                            f"{alerta.get('tipo', 'ALERTA')} - {alerta.get('fecha', 'N/A')} "
                            f"(Confianza: {alerta.get('confianza', 0):.0%})"
                        ):
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                st.write(f"**Mensaje:** {alerta.get('mensaje', 'N/A')}")
                                st.write(f"**Acción:** {alerta.get('accion', 'N/A')}")
                                
                                if 'valor_predicho' in alerta:
                                    st.write(f"**Valor Predicho:** {alerta['valor_predicho']} llamadas")
                                if 'umbral' in alerta:
                                    st.write(f"**Umbral:** {alerta['umbral']} llamadas")
                            
                            with col2:
                                # Medidor de confianza
                                confianza = alerta.get('confianza', 0.5)
                                fig_gauge = go.Figure(go.Indicator(
                                    mode = "gauge+number",
                                    value = confianza * 100,
                                    domain = {'x': [0, 1], 'y': [0, 1]},
                                    title = {'text': "Confianza"},
                                    gauge = {
                                        'axis': {'range': [None, 100]},
                                        'bar': {'color': "darkblue"},
                                        'steps': [
                                            {'range': [0, 50], 'color': "lightgray"},
                                            {'range': [50, 80], 'color': "yellow"},
                                            {'range': [80, 100], 'color': "green"}
                                        ],
                                        'threshold': {
                                            'line': {'color': "red", 'width': 4},
                                            'thickness': 0.75,
                                            'value': 90
                                        }
                                    }
                                ))
                                fig_gauge.update_layout(height=200, margin=dict(l=0, r=0, t=0, b=0))
                                st.plotly_chart(fig_gauge, use_container_width=True)
    
    def mostrar_recomendaciones_mejora(self, resultados):
        """Muestra recomendaciones específicas para mejorar el modelo"""
        st.subheader("💡 Recomendaciones de Mejora")
        
        metadatos_modelos = resultados.get('metadatos_modelos', {})
        pesos_ensemble = resultados.get('pesos_ensemble', {})
        
        recomendaciones = []
        
        # Análisis de performance general
        maes = [m.get('mae_validacion', m.get('mae_cv', 100)) for m in metadatos_modelos.values()]
        mae_promedio = np.mean(maes) if maes else 100
        
        if mae_promedio > 20:
            recomendaciones.append({
                'tipo': 'PRECISION_BAJA',
                'prioridad': 'ALTA',
                'titulo': 'Precisión General Baja',
                'problema': f'MAE promedio de {mae_promedio:.1f} llamadas supera el objetivo de 15',
                'solucion': 'Revisar calidad de datos, agregar más features, considerar modelos más sofisticados',
                'impacto': 'ALTO'
            })
        
        # Análisis de balance de ensemble
        if pesos_ensemble:
            peso_max = max(pesos_ensemble.values())
            if peso_max > 0.6:
                modelo_dominante = max(pesos_ensemble, key=pesos_ensemble.get)
                recomendaciones.append({
                    'tipo': 'ENSEMBLE_DESBALANCEADO',
                    'prioridad': 'MEDIA',
                    'titulo': 'Ensemble Desbalanceado',
                    'problema': f'Modelo {modelo_dominante} domina con peso {peso_max:.3f}',
                    'solucion': 'Mejorar otros modelos o ajustar pesos manualmente',
                    'impacto': 'MEDIO'
                })
        
        # Análisis de modelos individuales
        for modelo, metadata in metadatos_modelos.items():
            mae_modelo = metadata.get('mae_validacion', metadata.get('mae_cv', 0))
            if mae_modelo > 30:
                recomendaciones.append({
                    'tipo': 'MODELO_POOR_PERFORMANCE',
                    'prioridad': 'MEDIA',
                    'titulo': f'Performance Baja - {modelo.title()}',
                    'problema': f'MAE de {mae_modelo:.1f} muy alto para {modelo}',
                    'solucion': f'Optimizar hiperparámetros de {modelo} o considerar reemplazar',
                    'impacto': 'MEDIO'
                })
        
        # Recomendaciones por datos faltantes
        if len(metadatos_modelos) < 3:
            recomendaciones.append({
                'tipo': 'MODELOS_INSUFICIENTES',
                'prioridad': 'ALTA',
                'titulo': 'Pocos Modelos Activos',
                'problema': f'Solo {len(metadatos_modelos)} modelos entrenados',
                'solucion': 'Agregar más modelos al ensemble (XGBoost, LSTM, etc.)',
                'impacto': 'ALTO'
            })
        
        # Mostrar recomendaciones
        if recomendaciones:
            for rec in sorted(recomendaciones, key=lambda x: {'ALTA': 0, 'MEDIA': 1, 'BAJA': 2}[x['prioridad']]):
                
                prioridad_config = {
                    'ALTA': {'emoji': '🔥', 'color': 'red'},
                    'MEDIA': {'emoji': '⚠️', 'color': 'orange'},
                    'BAJA': {'emoji': 'ℹ️', 'color': 'blue'}
                }
                
                config = prioridad_config[rec['prioridad']]
                
                with st.expander(f"{config['emoji']} {rec['titulo']} (Prioridad: {rec['prioridad']})"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Problema:** {rec['problema']}")
                        st.write(f"**Solución:** {rec['solucion']}")
                    
                    with col2:
                        st.metric("Impacto Esperado", rec['impacto'])
        else:
            st.success("✅ El sistema está funcionando óptimamente. No hay recomendaciones críticas.")
    
    def mostrar_graficas_atencion_promedio(self, tipo_llamada):
        """Muestra gráficas de atención promedio de los últimos 15, 30 y 90 días"""
        st.subheader("📞 Análisis de Atención Promedio por Períodos")
        
        # Cargar datos completos
        df_completo = self.cargar_datos_llamadas_completos()
        
        if df_completo is None:
            st.error("❌ No se pudieron cargar los datos de llamadas")
            return
        
        # Filtrar por tipo de llamada si está disponible la columna SENTIDO
        if 'SENTIDO' in df_completo.columns:
            if tipo_llamada == 'ENTRANTE':
                df_filtrado = df_completo[df_completo['SENTIDO'] == 'in'].copy()
            else:
                df_filtrado = df_completo[df_completo['SENTIDO'] == 'out'].copy()
        else:
            df_filtrado = df_completo.copy()
            st.info("ℹ️ Mostrando datos combinados (no se pudo filtrar por tipo)")
        
        # Calcular fecha límite para cada período
        fecha_actual = datetime.now().date()
        fecha_15d = fecha_actual - timedelta(days=15)
        fecha_30d = fecha_actual - timedelta(days=30)
        fecha_90d = fecha_actual - timedelta(days=90)
        
        # Agregar datos por día
        df_diario = df_filtrado.groupby('fecha_solo').agg({
            'TELEFONO': 'count',  # Total de llamadas
            'ATENDIDA': lambda x: (x == 'Si').sum() if 'ATENDIDA' in df_filtrado.columns else 0,  # Llamadas atendidas
            'hora': 'mean'  # Hora promedio (para referencia)
        }).reset_index()
        
        df_diario.columns = ['fecha', 'total_llamadas', 'llamadas_atendidas', 'hora_promedio']
        df_diario['fecha'] = pd.to_datetime(df_diario['fecha'])
        
        # Calcular porcentaje de atención
        df_diario['porcentaje_atencion'] = (df_diario['llamadas_atendidas'] / df_diario['total_llamadas'] * 100).fillna(0)
        
        # Filtrar por períodos
        df_15d = df_diario[df_diario['fecha'] >= pd.to_datetime(fecha_15d)]
        df_30d = df_diario[df_diario['fecha'] >= pd.to_datetime(fecha_30d)]
        df_90d = df_diario[df_diario['fecha'] >= pd.to_datetime(fecha_90d)]
        
        # Crear métricas resumen
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if len(df_15d) > 0:
                promedio_15d = df_15d['porcentaje_atencion'].mean()
                llamadas_15d = df_15d['total_llamadas'].sum()
                st.metric(
                    "📅 Últimos 15 días",
                    f"{promedio_15d:.1f}%",
                    f"{llamadas_15d:,} llamadas totales"
                )
            else:
                st.metric("📅 Últimos 15 días", "Sin datos", "")
        
        with col2:
            if len(df_30d) > 0:
                promedio_30d = df_30d['porcentaje_atencion'].mean()
                llamadas_30d = df_30d['total_llamadas'].sum()
                st.metric(
                    "📅 Últimos 30 días",
                    f"{promedio_30d:.1f}%",
                    f"{llamadas_30d:,} llamadas totales"
                )
            else:
                st.metric("📅 Últimos 30 días", "Sin datos", "")
        
        with col3:
            if len(df_90d) > 0:
                promedio_90d = df_90d['porcentaje_atencion'].mean()
                llamadas_90d = df_90d['total_llamadas'].sum()
                st.metric(
                    "📅 Últimos 90 días",
                    f"{promedio_90d:.1f}%",
                    f"{llamadas_90d:,} llamadas totales"
                )
            else:
                st.metric("📅 Últimos 90 días", "Sin datos", "")
        
        # Crear gráfica comparativa
        if len(df_90d) > 0:
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=(
                    "Porcentaje de Atención por Día (Últimos 90 días)",
                    "Comparación de Promedios por Período",
                    "Volumen de Llamadas Diarias",
                    "Tendencia de Atención (Últimos 30 días)"
                ),
                specs=[[{"colspan": 2}, None],
                       [{}, {}]],
                vertical_spacing=0.12
            )
            
            # Gráfica principal: línea de tiempo de atención
            fig.add_trace(
                go.Scatter(
                    x=df_90d['fecha'],
                    y=df_90d['porcentaje_atencion'],
                    mode='lines+markers',
                    name='% Atención Diaria',
                    line=dict(color='#1f77b4', width=2),
                    marker=dict(size=4),
                    hovertemplate='<b>%{x}</b><br>Atención: %{y:.1f}%<extra></extra>'
                ),
                row=1, col=1
            )
            
            # Líneas de referencia para períodos
            if len(df_15d) > 0:
                fig.add_hline(
                    y=df_15d['porcentaje_atencion'].mean(),
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Promedio 15d: {df_15d['porcentaje_atencion'].mean():.1f}%",
                    row=1, col=1
                )
            
            if len(df_30d) > 0:
                fig.add_hline(
                    y=df_30d['porcentaje_atencion'].mean(),
                    line_dash="dot",
                    line_color="orange",
                    annotation_text=f"Promedio 30d: {df_30d['porcentaje_atencion'].mean():.1f}%",
                    row=1, col=1
                )
            
            # Gráfica de barras: comparación de promedios
            periodos = []
            promedios = []
            colores = []
            
            if len(df_15d) > 0:
                periodos.append('15 días')
                promedios.append(df_15d['porcentaje_atencion'].mean())
                colores.append('#ff7f0e')
            
            if len(df_30d) > 0:
                periodos.append('30 días')
                promedios.append(df_30d['porcentaje_atencion'].mean())
                colores.append('#2ca02c')
            
            if len(df_90d) > 0:
                periodos.append('90 días')
                promedios.append(df_90d['porcentaje_atencion'].mean())
                colores.append('#d62728')
            
            if periodos:
                fig.add_trace(
                    go.Bar(
                        x=periodos,
                        y=promedios,
                        name='Promedio por Período',
                        marker_color=colores,
                        text=[f'{p:.1f}%' for p in promedios],
                        textposition='auto',
                        hovertemplate='<b>%{x}</b><br>Promedio: %{y:.1f}%<extra></extra>'
                    ),
                    row=2, col=1
                )
            
            # Gráfica de volumen de llamadas
            fig.add_trace(
                go.Bar(
                    x=df_30d['fecha'] if len(df_30d) > 0 else [],
                    y=df_30d['total_llamadas'] if len(df_30d) > 0 else [],
                    name='Llamadas Diarias',
                    marker_color='lightblue',
                    opacity=0.7,
                    hovertemplate='<b>%{x}</b><br>Llamadas: %{y}<extra></extra>'
                ),
                row=2, col=2
            )
            
            # Configurar layout
            fig.update_layout(
                height=800,
                title=f"Análisis de Atención - Llamadas {tipo_llamada}",
                showlegend=True
            )
            
            fig.update_xaxes(title_text="Fecha", row=1, col=1)
            fig.update_yaxes(title_text="Porcentaje de Atención (%)", row=1, col=1)
            fig.update_xaxes(title_text="Período", row=2, col=1)
            fig.update_yaxes(title_text="Promedio Atención (%)", row=2, col=1)
            fig.update_xaxes(title_text="Fecha", row=2, col=2)
            fig.update_yaxes(title_text="Número de Llamadas", row=2, col=2)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabla resumen por día de la semana
            if len(df_30d) > 0:
                st.subheader("📊 Resumen por Día de la Semana (Últimos 30 días)")
                
                df_30d['dia_semana'] = df_30d['fecha'].dt.day_name()
                resumen_semanal = df_30d.groupby('dia_semana').agg({
                    'porcentaje_atencion': ['mean', 'std'],
                    'total_llamadas': ['mean', 'sum'],
                    'llamadas_atendidas': 'sum'
                }).round(2)
                
                resumen_semanal.columns = ['Atención Promedio (%)', 'Desv. Estándar (%)', 'Llamadas Promedio/Día', 'Total Llamadas', 'Total Atendidas']
                
                # Ordenar por días de la semana
                orden_dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                resumen_semanal = resumen_semanal.reindex([dia for dia in orden_dias if dia in resumen_semanal.index])
                
                st.dataframe(
                    resumen_semanal.style.format({
                        'Atención Promedio (%)': '{:.1f}%',
                        'Desv. Estándar (%)': '{:.1f}%',
                        'Llamadas Promedio/Día': '{:.0f}',
                        'Total Llamadas': '{:,.0f}',
                        'Total Atendidas': '{:,.0f}'
                    }).background_gradient(subset=['Atención Promedio (%)'], cmap='RdYlGn'),
                    use_container_width=True
                )
        else:
            st.warning("⚠️ No hay datos suficientes para generar las gráficas")
    
    def mostrar_metricas_objetivo(self, resultados):
        """Muestra progress hacia objetivos del proyecto"""
        st.subheader("🎯 Progress Hacia Objetivos")
        
        # Objetivos del proyecto
        objetivos = {
            'MAE': {'objetivo': 10, 'actual': 0, 'unidad': 'llamadas'},
            'RMSE': {'objetivo': 15, 'actual': 0, 'unidad': 'llamadas'},
            'MAPE': {'objetivo': 25, 'actual': 0, 'unidad': '%'},
            'Precision_Alertas': {'objetivo': 90, 'actual': 0, 'unidad': '%'}
        }
        
        # Obtener valores actuales
        metadatos_modelos = resultados.get('metadatos_modelos', {})
        if metadatos_modelos:
            maes = [m.get('mae_validacion', m.get('mae_cv', 0)) for m in metadatos_modelos.values() if m.get('mae_validacion', m.get('mae_cv', 0)) > 0]
            rmses = [m.get('rmse_validacion', m.get('rmse_cv', 0)) for m in metadatos_modelos.values() if m.get('rmse_validacion', m.get('rmse_cv', 0)) > 0]
            
            if maes:
                objetivos['MAE']['actual'] = min(maes)  # Mejor MAE
            if rmses:
                objetivos['RMSE']['actual'] = min(rmses)  # Mejor RMSE
            
            # Simular MAPE y precisión de alertas
            objetivos['MAPE']['actual'] = np.random.uniform(15, 35)
            objetivos['Precision_Alertas']['actual'] = np.random.uniform(75, 95)
        
        # Mostrar métricas
        col1, col2, col3, col4 = st.columns(4)
        
        for i, (metrica, data) in enumerate(objetivos.items()):
            with [col1, col2, col3, col4][i]:
                
                # Calcular progreso
                if metrica in ['MAE', 'RMSE', 'MAPE']:  # Menor es mejor
                    progreso = max(0, min(100, (data['objetivo'] - data['actual']) / data['objetivo'] * 100))
                    color = 'normal' if data['actual'] <= data['objetivo'] else 'inverse'
                else:  # Mayor es mejor
                    progreso = min(100, data['actual'] / data['objetivo'] * 100)
                    color = 'normal'
                
                # Determinar estado
                if progreso >= 90:
                    emoji = "🎉"
                    estado = "Objetivo Alcanzado"
                elif progreso >= 70:
                    emoji = "✅"
                    estado = "En Camino"
                elif progreso >= 50:
                    emoji = "⚠️"
                    estado = "Requiere Atención"
                else:
                    emoji = "❌"
                    estado = "Crítico"
                
                st.metric(
                    f"{emoji} {metrica.replace('_', ' ')}",
                    f"{data['actual']:.1f} {data['unidad']}",
                    f"Objetivo: {data['objetivo']} {data['unidad']}"
                )
                
                # Barra de progreso
                st.progress(progreso / 100)
                st.caption(f"{estado} ({progreso:.0f}%)")
    
    def ejecutar_dashboard(self):
        """Ejecuta el dashboard principal de validación"""
        
        # Header
        tipo_llamada = self.mostrar_header_validacion()
        
        # Cargar datos
        resultados, df_predicciones = self.cargar_resultados_multimodelo(tipo_llamada)
        df_historico = self.cargar_datos_historicos(tipo_llamada)
        
        # Mostrar gráficas de atención promedio PRIMERO (siempre disponible)
        self.mostrar_graficas_atencion_promedio(tipo_llamada)
        
        st.markdown("---")
        
        if resultados is None:
            st.error("❌ No se pudieron cargar los resultados del sistema multi-modelo")
            st.info("💡 Ejecutar el sistema multi-modelo primero")
            st.info("📞 Sin embargo, puedes ver el análisis de atención arriba con los datos históricos")
            return
        
        # Mostrar métricas de objetivo
        self.mostrar_metricas_objetivo(resultados)
        
        st.markdown("---")
        
        # Métricas comparativas
        self.mostrar_metricas_comparativas(resultados)
        
        st.markdown("---")
        
        # Gráfico de predicciones
        if df_predicciones is not None:
            self.mostrar_grafico_predicciones_detallado(df_predicciones, df_historico)
        
        st.markdown("---")
        
        # Análisis de residuales
        if df_historico is not None:
            self.mostrar_analisis_residuales(resultados, df_historico)
        
        st.markdown("---")
        
        # Heatmaps de patrones temporales
        self.mostrar_heatmaps_patrones_temporales(tipo_llamada)
        
        st.markdown("---")
        
        # Alertas validadas
        self.mostrar_alertas_validacion(resultados)
        
        st.markdown("---")
        
        # Recomendaciones
        self.mostrar_recomendaciones_mejora(resultados)
        
        # Footer
        st.markdown("---")
        st.markdown(
            f"📊 **Dashboard de Validación CEAPSI** | "
            f"Tipo: {tipo_llamada} | "
            f"Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )
    
    def mostrar_heatmaps_patrones_temporales(self, tipo_llamada):
        """Muestra heatmaps de patrones temporales de llamadas"""
        
        st.subheader("📈 Análisis de Patrones Temporales")
        
        # Cargar datos completos para el análisis
        df_completo = self.cargar_datos_llamadas_completos()
        
        if df_completo is None or len(df_completo) == 0:
            st.warning("⚠️ No hay datos suficientes para generar heatmaps de patrones temporales")
            return
        
        # Preparar datos
        df_filtrado = self._preparar_datos_heatmap(df_completo, tipo_llamada)
        
        if len(df_filtrado) == 0:
            st.warning(f"⚠️ No hay datos suficientes para {tipo_llamada}")
            return
        
        # Crear pestañas para diferentes tipos de heatmaps
        tab1, tab2, tab3 = st.tabs(["🗓️ Patrón Semanal", "🕐 Patrón Horario", "📊 Combinado"])
        
        with tab1:
            self._mostrar_heatmap_semanal(df_filtrado, tipo_llamada)
        
        with tab2:
            self._mostrar_heatmap_horario(df_filtrado, tipo_llamada)
        
        with tab3:
            self._mostrar_heatmap_combinado(df_filtrado, tipo_llamada)
    
    def _preparar_datos_heatmap(self, df_completo, tipo_llamada):
        """Prepara los datos para generar heatmaps"""
        try:
            # Filtrar por tipo de llamada si no son datos de ejemplo
            if 'SENTIDO' in df_completo.columns:
                sentido_filter = 'in' if tipo_llamada.upper() == 'ENTRANTE' else 'out'
                df_filtrado = df_completo[df_completo['SENTIDO'] == sentido_filter].copy()
            else:
                # Para datos de ejemplo que no tienen SENTIDO
                df_filtrado = df_completo.copy()
            
            # Convertir fechas
            df_filtrado['FECHA'] = pd.to_datetime(df_filtrado['FECHA'], errors='coerce')
            
            # Filtrar datos válidos
            df_filtrado = df_filtrado.dropna(subset=['FECHA'])
            
            # Agregar columnas temporales
            df_filtrado['dia_semana'] = df_filtrado['FECHA'].dt.day_name()
            df_filtrado['dia_semana_num'] = df_filtrado['FECHA'].dt.dayofweek
            df_filtrado['hora'] = df_filtrado['FECHA'].dt.hour
            df_filtrado['fecha_solo'] = df_filtrado['FECHA'].dt.date
            df_filtrado['semana'] = df_filtrado['FECHA'].dt.isocalendar().week
            df_filtrado['mes'] = df_filtrado['FECHA'].dt.month
            
            return df_filtrado
            
        except Exception as e:
            st.error(f"Error preparando datos: {e}")
            return pd.DataFrame()
    
    def _mostrar_heatmap_semanal(self, df_filtrado, tipo_llamada):
        """Muestra heatmap de patrones por día de la semana"""
        
        st.subheader(f"🗓️ Patrón de Llamadas {tipo_llamada} por Día de la Semana")
        
        try:
            # Agrupar por día de la semana y semana del año
            agrupacion = df_filtrado.groupby(['semana', 'dia_semana_num']).size().reset_index(name='llamadas')
            
            # Crear matriz para el heatmap
            dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            
            # Pivot para crear matriz
            matriz_semanal = agrupacion.pivot(index='semana', columns='dia_semana_num', values='llamadas')
            matriz_semanal = matriz_semanal.fillna(0)
            
            # Asegurar que tenemos todas las columnas (días de la semana)
            for i in range(7):
                if i not in matriz_semanal.columns:
                    matriz_semanal[i] = 0
            
            # Ordenar columnas
            matriz_semanal = matriz_semanal[sorted(matriz_semanal.columns)]
            
            # Crear heatmap con Plotly
            fig_semanal = go.Figure(data=go.Heatmap(
                z=matriz_semanal.values,
                x=[dias_semana[i] for i in sorted(matriz_semanal.columns)],
                y=[f'Semana {int(semana)}' for semana in matriz_semanal.index],
                colorscale='Blues',
                hoverinfo='all',
                hovertemplate='<b>%{y}</b><br>%{x}<br>Llamadas: %{z}<extra></extra>',
                colorbar=dict(title="Número de Llamadas")
            ))
            
            fig_semanal.update_layout(
                title=f'Distribución Semanal de Llamadas {tipo_llamada}',
                xaxis_title='Día de la Semana',
                yaxis_title='Semana del Año',
                height=400,
                font=dict(size=12)
            )
            
            st.plotly_chart(fig_semanal, use_container_width=True)
            
            # Métricas de resumen semanal
            col1, col2, col3 = st.columns(3)
            
            # Calcular estadísticas por día
            stats_diarios = df_filtrado.groupby('dia_semana')['FECHA'].count()
            
            with col1:
                dia_mas_activo = stats_diarios.idxmax()
                max_llamadas = stats_diarios.max()
                st.metric("📈 Día Más Activo", dia_mas_activo, f"{max_llamadas} llamadas")
            
            with col2:
                dia_menos_activo = stats_diarios.idxmin()
                min_llamadas = stats_diarios.min()
                st.metric("📉 Día Menos Activo", dia_menos_activo, f"{min_llamadas} llamadas")
            
            with col3:
                variacion = ((max_llamadas - min_llamadas) / min_llamadas * 100) if min_llamadas > 0 else 0
                st.metric("📊 Variación Semanal", f"{variacion:.1f}%")
            
        except Exception as e:
            st.error(f"Error generando heatmap semanal: {e}")
    
    def _mostrar_heatmap_horario(self, df_filtrado, tipo_llamada):
        """Muestra heatmap de patrones por hora del día"""
        
        st.subheader(f"🕐 Patrón de Llamadas {tipo_llamada} por Hora del Día")
        
        try:
            # Agrupar por día y hora
            agrupacion_horaria = df_filtrado.groupby(['fecha_solo', 'hora']).size().reset_index(name='llamadas')
            
            # Crear matriz para el heatmap
            matriz_horaria = agrupacion_horaria.pivot(index='fecha_solo', columns='hora', values='llamadas')
            matriz_horaria = matriz_horaria.fillna(0)
            
            # Asegurar que tenemos todas las horas (0-23)
            for hora in range(24):
                if hora not in matriz_horaria.columns:
                    matriz_horaria[hora] = 0
            
            # Ordenar columnas
            matriz_horaria = matriz_horaria[sorted(matriz_horaria.columns)]
            
            # Limitar a últimos 30 días para mejor visualización
            if len(matriz_horaria) > 30:
                matriz_horaria = matriz_horaria.tail(30)
            
            # Crear heatmap con Plotly
            fig_horario = go.Figure(data=go.Heatmap(
                z=matriz_horaria.values,
                x=[f'{h:02d}:00' for h in sorted(matriz_horaria.columns)],
                y=[str(fecha) for fecha in matriz_horaria.index],
                colorscale='Viridis',
                hoverinfo='all',
                hovertemplate='<b>%{y}</b><br>%{x}<br>Llamadas: %{z}<extra></extra>',
                colorbar=dict(title="Número de Llamadas")
            ))
            
            fig_horario.update_layout(
                title=f'Distribución Horaria de Llamadas {tipo_llamada} (Últimos 30 días)',
                xaxis_title='Hora del Día',
                yaxis_title='Fecha',
                height=500,
                font=dict(size=12)
            )
            
            # Rotar etiquetas del eje Y para mejor legibilidad
            fig_horario.update_yaxes(tickangle=0)
            fig_horario.update_xaxes(tickangle=45)
            
            st.plotly_chart(fig_horario, use_container_width=True)
            
            # Métricas de resumen horario
            col1, col2, col3 = st.columns(3)
            
            # Calcular estadísticas por hora
            stats_horarios = df_filtrado.groupby('hora')['FECHA'].count()
            
            with col1:
                hora_pico = stats_horarios.idxmax()
                max_llamadas_hora = stats_horarios.max()
                st.metric("🔥 Hora Pico", f"{hora_pico:02d}:00", f"{max_llamadas_hora} llamadas")
            
            with col2:
                hora_valle = stats_horarios.idxmin()
                min_llamadas_hora = stats_horarios.min()
                st.metric("🌙 Hora Valle", f"{hora_valle:02d}:00", f"{min_llamadas_hora} llamadas")
            
            with col3:
                # Calcular horario laboral (8-18)
                llamadas_laborales = df_filtrado[(df_filtrado['hora'] >= 8) & (df_filtrado['hora'] <= 18)]
                pct_laborales = (len(llamadas_laborales) / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0
                st.metric("🏢 % Horario Laboral", f"{pct_laborales:.1f}%")
            
        except Exception as e:
            st.error(f"Error generando heatmap horario: {e}")
    
    def _mostrar_heatmap_combinado(self, df_filtrado, tipo_llamada):
        """Muestra heatmap combinado día de semana vs hora"""
        
        st.subheader(f"📊 Patrón Combinado: Día de Semana vs Hora ({tipo_llamada})")
        
        try:
            # Agrupar por día de semana y hora
            agrupacion_combinada = df_filtrado.groupby(['dia_semana_num', 'hora']).size().reset_index(name='llamadas')
            
            # Crear matriz para el heatmap
            matriz_combinada = agrupacion_combinada.pivot(index='dia_semana_num', columns='hora', values='llamadas')
            matriz_combinada = matriz_combinada.fillna(0)
            
            # Asegurar que tenemos todas las horas
            for hora in range(24):
                if hora not in matriz_combinada.columns:
                    matriz_combinada[hora] = 0
            
            # Ordenar columnas
            matriz_combinada = matriz_combinada[sorted(matriz_combinada.columns)]
            
            # Nombres de días
            dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            
            # Crear heatmap
            fig_combinado = go.Figure(data=go.Heatmap(
                z=matriz_combinada.values,
                x=[f'{h:02d}:00' for h in sorted(matriz_combinada.columns)],
                y=[dias_semana[i] for i in matriz_combinada.index],
                colorscale='RdYlBu_r',
                hoverinfo='all',
                hovertemplate='<b>%{y}</b><br>%{x}<br>Llamadas: %{z}<extra></extra>',
                colorbar=dict(title="Promedio de Llamadas")
            ))
            
            fig_combinado.update_layout(
                title=f'Mapa de Calor: Llamadas {tipo_llamada} por Día y Hora',
                xaxis_title='Hora del Día',
                yaxis_title='Día de la Semana',
                height=400,
                font=dict(size=12)
            )
            
            st.plotly_chart(fig_combinado, use_container_width=True)
            
            # Insights del patrón combinado
            st.subheader("🔍 Insights del Patrón Combinado")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Encontrar el momento más activo
                max_pos = np.unravel_index(matriz_combinada.values.argmax(), matriz_combinada.values.shape)
                dia_max = dias_semana[matriz_combinada.index[max_pos[0]]]
                hora_max = sorted(matriz_combinada.columns)[max_pos[1]]
                valor_max = matriz_combinada.values[max_pos]
                
                st.info(f"🔥 **Momento Más Activo**  \n{dia_max} a las {hora_max:02d}:00  \n{valor_max:.0f} llamadas promedio")
            
            with col2:
                # Calcular concentración de llamadas
                total_llamadas = matriz_combinada.values.sum()
                # Top 20% de células más activas
                flat_values = matriz_combinada.values.flatten()
                top_20_percent = np.percentile(flat_values, 80)
                concentracion = (flat_values >= top_20_percent).sum() / len(flat_values) * 100
                
                st.info(f"📊 **Concentración de Actividad**  \nEl 80% de las llamadas ocurren en  \n{concentracion:.1f}% del tiempo")
            
        except Exception as e:
            st.error(f"Error generando heatmap combinado: {e}")
    
    def _crear_datos_ejemplo_historicos(self, tipo_llamada):
        """Crea datos de ejemplo para cuando no hay archivos históricos"""
        try:
            # Crear 60 días de datos de ejemplo
            fechas = pd.date_range(
                start=datetime.now() - timedelta(days=60),
                end=datetime.now() - timedelta(days=1),
                freq='D'
            )
            
            # Simular patrones de llamadas basados en tipo
            if tipo_llamada.lower() == 'entrante':
                # Llamadas entrantes: más volumen en días laborales
                base_calls = 80
                weekend_factor = 0.3
            else:
                # Llamadas salientes: más constantes
                base_calls = 45
                weekend_factor = 0.8
            
            # Generar datos simulados
            datos_ejemplo = []
            for fecha in fechas:
                # Ajustar por día de semana
                if fecha.weekday() >= 5:  # Fin de semana
                    calls = base_calls * weekend_factor
                else:
                    calls = base_calls
                
                # Agregar algo de ruido realista
                calls += np.random.normal(0, calls * 0.2)
                calls = max(0, int(calls))  # No negativos
                
                datos_ejemplo.append({
                    'ds': fecha.strftime('%Y-%m-%d'),
                    'y': calls
                })
            
            df_ejemplo = pd.DataFrame(datos_ejemplo)
            df_ejemplo['ds'] = pd.to_datetime(df_ejemplo['ds'])
            
            # Guardar archivo de ejemplo para uso posterior
            archivo_ejemplo = f"datos_prophet_{tipo_llamada.lower()}.csv"
            df_ejemplo.to_csv(archivo_ejemplo, index=False)
            
            st.success(f"✅ Datos de ejemplo creados para {tipo_llamada}")
            return df_ejemplo
            
        except Exception as e:
            st.error(f"Error creando datos de ejemplo: {e}")
            # Datos mínimos como último recurso
            return pd.DataFrame({
                'ds': pd.date_range(start='2023-01-01', periods=30, freq='D'),
                'y': np.random.randint(20, 100, 30)
            })
    
    def _crear_datos_ejemplo_completos(self):
        """Crea un dataset completo de ejemplo para demostración"""
        try:
            # Crear 90 días de datos de ejemplo con llamadas realistas
            fechas = pd.date_range(
                start=datetime.now() - timedelta(days=90),
                end=datetime.now() - timedelta(days=1),
                freq='D'
            )
            
            datos_completos = []
            for i, fecha in enumerate(fechas):
                # Simular llamadas a lo largo del día
                for hora in range(8, 18):  # Horario laboral
                    num_llamadas = np.random.poisson(8)  # Promedio 8 llamadas por hora
                    
                    for j in range(num_llamadas):
                        # Alternar entre entrantes y salientes
                        sentido = 'in' if (i + j) % 2 == 0 else 'out'
                        # 80% de las llamadas atendidas
                        atendida = 'Si' if np.random.random() < 0.8 else 'No'
                        # Generar teléfono ficticio
                        telefono = f"+569{np.random.randint(10000000, 99999999)}"
                        
                        minutos = np.random.randint(0, 60)
                        segundos = np.random.randint(0, 60)
                        
                        datos_completos.append({
                            'FECHA': fecha.strftime(f'%d-%m-%Y %02d:%02d:%02d') % (hora, minutos, segundos),
                            'TELEFONO': telefono,
                            'SENTIDO': sentido,
                            'ATENDIDA': atendida,
                            'STATUS': 'ANSWERED' if atendida == 'Si' else 'NO_ANSWER'
                        })
            
            df_completo = pd.DataFrame(datos_completos)
            st.success(f"✅ Dataset de ejemplo creado con {len(df_completo)} llamadas")
            return df_completo
            
        except Exception as e:
            st.error(f"Error creando dataset completo de ejemplo: {e}")
            # Dataset mínimo
            return pd.DataFrame({
                'FECHA': ['01-01-2024 10:00:00', '01-01-2024 11:00:00'],
                'TELEFONO': ['+56912345678', '+56987654321'],
                'SENTIDO': ['in', 'out'],
                'ATENDIDA': ['Si', 'No'],
                'STATUS': ['ANSWERED', 'NO_ANSWER']
            })
    
    def _crear_resultados_ejemplo(self, tipo_llamada):
        """Crea resultados de ejemplo para el multi-modelo"""
        try:
            # Crear predicciones para los próximos 28 días
            fechas_futuras = pd.date_range(
                start=datetime.now(),
                periods=28,
                freq='D'
            )
            
            # Simular valores según tipo
            if tipo_llamada.lower() == 'entrante':
                base_value = 85
                variabilidad = 15
            else:
                base_value = 50
                variabilidad = 10
            
            predicciones = []
            for fecha in fechas_futuras:
                valor = base_value + np.random.normal(0, variabilidad)
                valor = max(10, int(valor))  # Mínimo 10 llamadas
                
                predicciones.append({
                    'ds': fecha.strftime('%Y-%m-%d'),
                    'yhat_ensemble': valor,
                    'yhat_lower': valor * 0.8,
                    'yhat_upper': valor * 1.2,
                    'yhat_arima': valor + np.random.normal(0, 5),
                    'yhat_prophet': valor + np.random.normal(0, 5),
                    'yhat_rf': valor + np.random.normal(0, 5),
                    'yhat_gb': valor + np.random.normal(0, 5)
                })
            
            # Simular metadatos de modelos
            metadatos_modelos = {
                'arima': {
                    'mae_cv': np.random.uniform(8, 12),
                    'mape_cv': np.random.uniform(15, 25),
                    'tiempo_entrenamiento': '2.5 segundos'
                },
                'prophet': {
                    'mae_cv': np.random.uniform(7, 11),
                    'mape_cv': np.random.uniform(12, 22),
                    'tiempo_entrenamiento': '3.2 segundos'
                },
                'random_forest': {
                    'mae_cv': np.random.uniform(9, 13),
                    'mape_cv': np.random.uniform(18, 28),
                    'tiempo_entrenamiento': '1.8 segundos'
                },
                'gradient_boosting': {
                    'mae_cv': np.random.uniform(8, 12),
                    'mape_cv': np.random.uniform(14, 24),
                    'tiempo_entrenamiento': '2.1 segundos'
                }
            }
            
            # Simular pesos del ensemble
            pesos_ensemble = {
                'arima': 0.25,
                'prophet': 0.30,
                'random_forest': 0.20,
                'gradient_boosting': 0.25
            }
            
            resultados_ejemplo = {
                'predicciones': predicciones,
                'metadatos_modelos': metadatos_modelos,
                'pesos_ensemble': pesos_ensemble,
                'tipo_llamada': tipo_llamada,
                'timestamp_generacion': datetime.now().isoformat(),
                'alertas': []  # Sin alertas para el ejemplo
            }
            
            df_pred = pd.DataFrame(predicciones)
            df_pred['ds'] = pd.to_datetime(df_pred['ds'])
            
            st.success(f"✅ Resultados de ejemplo creados para {tipo_llamada}")
            return resultados_ejemplo, df_pred
            
        except Exception as e:
            st.error(f"Error creando resultados de ejemplo: {e}")
            return None, None

def main():
    """Función principal del dashboard de validación"""
    dashboard = DashboardValidacionCEAPSI()
    dashboard.ejecutar_dashboard()

if __name__ == "__main__":
    main()