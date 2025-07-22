#!/usr/bin/env python3
"""
UX Improvements for CEAPSI Dashboard
Mejoras de experiencia de usuario para el dashboard CEAPSI
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
from pathlib import Path

def mostrar_progreso_pipeline():
    """Muestra el progreso visual del pipeline de manera clara"""
    st.markdown("### 📋 Estado del Pipeline")
    
    # Definir pasos del pipeline
    pasos = [
        {"nombre": "Cargar Datos", "icono": "📁", "completado": st.session_state.get('datos_cargados', False)},
        {"nombre": "Validar Estructura", "icono": "🔍", "completado": st.session_state.get('datos_validados', False)},
        {"nombre": "Procesar Datos", "icono": "⚙️", "completado": st.session_state.get('datos_procesados', False)},
        {"nombre": "Entrenar Modelos", "icono": "🤖", "completado": st.session_state.get('modelos_entrenados', False)},
        {"nombre": "Generar Predicciones", "icono": "🔮", "completado": st.session_state.get('predicciones_generadas', False)},
        {"nombre": "Visualizar Resultados", "icono": "📊", "completado": st.session_state.get('pipeline_completado', False)}
    ]
    
    # Crear indicador visual de progreso
    cols = st.columns(len(pasos))
    
    for i, (col, paso) in enumerate(zip(cols, pasos)):
        with col:
            if paso["completado"]:
                st.success(f"{paso['icono']} {paso['nombre']}")
            elif i == 0 or pasos[i-1]["completado"]:
                st.warning(f"{paso['icono']} {paso['nombre']}")
            else:
                st.info(f"⏳ {paso['nombre']}")
    
    # Barra de progreso general
    completados = sum(1 for paso in pasos if paso["completado"])
    progreso = completados / len(pasos)
    
    st.progress(progreso)
    st.caption(f"Progreso: {completados}/{len(pasos)} pasos completados ({progreso*100:.0f}%)")
    
    return completados, len(pasos)

def mostrar_card_metrica(titulo, valor, descripcion, icono, color="blue", delta=None):
    """Crea una card de métrica visualmente atractiva"""
    delta_html = ""
    if delta is not None:
        delta_color = "green" if delta >= 0 else "red"
        delta_symbol = "↑" if delta >= 0 else "↓"
        delta_html = f'<p style="color: {delta_color}; margin: 5px 0;">{delta_symbol} {abs(delta):.1f}%</p>'
    
    card_html = f"""
    <div style="
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 20px;
        background: linear-gradient(135deg, {color}20, {color}10);
        border-left: 5px solid {color};
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        height: 140px;
    ">
        <div style="display: flex; align-items: center; margin-bottom: 10px;">
            <span style="font-size: 24px; margin-right: 10px;">{icono}</span>
            <h4 style="margin: 0; color: #333;">{titulo}</h4>
        </div>
        <h2 style="margin: 10px 0; color: {color}; font-weight: bold;">{valor}</h2>
        {delta_html}
        <p style="margin: 0; color: #666; font-size: 12px;">{descripcion}</p>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

def mostrar_onboarding_mejorado():
    """Sistema de onboarding mejorado para nuevos usuarios"""
    
    # Verificar si es primera vez
    if not st.session_state.get('onboarding_completado', False):
        
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 30px;
        ">
            <h1>🎉 ¡Bienvenido a CEAPSI!</h1>
            <h3>Sistema de Predicción de Llamadas con IA</h3>
            <p>Te guiaremos paso a paso para comenzar tu análisis</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Tabs de onboarding
        tab1, tab2, tab3 = st.tabs(["🚀 Empezar", "📖 Guía Rápida", "💡 Consejos"])
        
        with tab1:
            st.markdown("### 🎯 ¿Qué quieres hacer hoy?")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📈 Analizar mis llamadas", use_container_width=True, type="primary"):
                    st.session_state.objetivo_usuario = "analizar"
                    st.rerun()
            
            with col2:
                if st.button("🔧 Preparar datos nuevos", use_container_width=True):
                    st.session_state.objetivo_usuario = "preparar"
                    st.rerun()
            
            with col3:
                if st.button("🎯 Optimizar modelos", use_container_width=True):
                    st.session_state.objetivo_usuario = "optimizar"
                    st.rerun()
        
        with tab2:
            st.markdown("""
            ### 📚 Guía de 3 Minutos
            
            **Paso 1: Carga tus datos** 📁
            - Sube un archivo CSV o Excel con datos de llamadas
            - El sistema detectará automáticamente las columnas
            
            **Paso 2: Ejecuta el pipeline** 🚀
            - Haz clic en "Ejecutar Pipeline Completo"
            - Espera a que se procesen y entrenen los modelos
            
            **Paso 3: Explora resultados** 📊
            - Ve al Dashboard para ver predicciones
            - Analiza patrones temporales y heatmaps
            """)
        
        with tab3:
            st.markdown("""
            ### 💡 Consejos Pro
            
            **Para mejores resultados:**
            - ✅ Usa al menos 30 días de datos históricos
            - ✅ Asegúrate de que las fechas estén en formato correcto
            - ✅ Incluye datos de fines de semana si es relevante
            
            **Columnas necesarias:**
            - `FECHA`: Fecha y hora de la llamada
            - `TELEFONO`: Número de teléfono
            - `SENTIDO`: 'in' (entrante) o 'out' (saliente)
            - `ATENDIDA`: 'Si' o 'No'
            """)
        
        if st.button("✅ Completar Onboarding"):
            st.session_state.onboarding_completado = True
            st.success("¡Perfecto! Ya puedes usar CEAPSI")
            time.sleep(1)
            st.rerun()
    
    return st.session_state.get('objetivo_usuario', None)

def mostrar_navegacion_contextual():
    """Navegación contextual basada en el estado del sistema"""
    
    # Obtener estado actual
    datos_cargados = st.session_state.get('datos_cargados', False)
    pipeline_completado = st.session_state.get('pipeline_completado', False)
    
    st.markdown("### 🧭 ¿Qué hacer ahora?")
    
    if not datos_cargados:
        st.info("👆 **Próximo paso:** Carga un archivo de datos usando el panel lateral")
        
        with st.expander("💡 ¿Necesitas ayuda preparando datos?"):
            st.markdown("""
            - **🔧 Preparación de Datos**: Valida y limpia tus archivos
            - **📋 Formato requerido**: CSV/Excel con columnas específicas
            - **🔌 API Reservo**: Conecta con sistemas externos
            """)
            
            if st.button("Ir a Preparación de Datos"):
                st.session_state.pagina_activa = "🔧 Preparación de Datos"
                st.rerun()
    
    elif not pipeline_completado:
        st.warning("⚙️ **Próximo paso:** Ejecuta el pipeline para procesar los datos")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 Ejecutar Pipeline", type="primary", use_container_width=True):
                # Aquí iría la lógica del pipeline
                st.session_state.ejecutar_pipeline = True
        
        with col2:
            if st.button("📊 Ver datos cargados", use_container_width=True):
                # Mostrar preview de datos
                st.session_state.mostrar_preview = True
    
    else:
        st.success("🎉 **¡Todo listo!** Explora tus resultados")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Ver Dashboard", use_container_width=True, type="primary"):
                st.session_state.pagina_activa = "📊 Dashboard"
                st.rerun()
        
        with col2:
            if st.button("🎯 Optimizar ML", use_container_width=True):
                st.session_state.pagina_activa = "🎯 Optimización ML"
                st.rerun()
        
        with col3:
            if st.button("👥 Análisis Usuarios", use_container_width=True):
                st.session_state.pagina_activa = "👥 Análisis de Usuarios"
                st.rerun()

def mostrar_dashboard_mejorado():
    """Dashboard principal con UX mejorada"""
    
    # Header con contexto claro
    st.markdown("""
    <div style="
        background: linear-gradient(90deg, #4CAF50, #45a049);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    ">
        <h2 style="margin: 0;">📊 Dashboard de Análisis</h2>
        <p style="margin: 5px 0 0 0;">Resultados de predicción y análisis de patrones</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Resumen ejecutivo en cards
    st.markdown("### 📈 Resumen Ejecutivo")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        mostrar_card_metrica(
            "Total Llamadas", "1,234", 
            "Últimos 30 días", "📞", 
            color="#4CAF50", delta=12.5
        )
    
    with col2:
        mostrar_card_metrica(
            "Tasa Atención", "87.3%", 
            "Promedio mensual", "✅", 
            color="#2196F3", delta=-2.1
        )
    
    with col3:
        mostrar_card_metrica(
            "Pico Diario", "156", 
            "Máximo por día", "📈", 
            color="#FF9800", delta=8.7
        )
    
    with col4:
        mostrar_card_metrica(
            "Precisión IA", "94.2%", 
            "Modelos entrenados", "🤖", 
            color="#9C27B0", delta=1.3
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tabs organizados por audiencia
    tab_gerencial, tab_operativo, tab_tecnico = st.tabs([
        "👔 Vista Gerencial", 
        "⚡ Vista Operativa", 
        "🔬 Vista Técnica"
    ])
    
    with tab_gerencial:
        st.markdown("### 📊 KPIs Ejecutivos")
        
        # Gráfico de tendencia simplificado
        fig_trend = go.Figure()
        
        # IMPORTANTE: Usar fechas fijas para evitar data leakage en demos científicas
        fechas = pd.date_range(start='2023-01-01', periods=30, freq='D')
        llamadas = [100 + i*2 + np.random.randint(-10, 10) for i in range(30)]
        
        fig_trend.add_trace(go.Scatter(
            x=fechas,
            y=llamadas,
            mode='lines+markers',
            name='Llamadas Diarias',
            line=dict(color='#4CAF50', width=3),
            marker=dict(size=8)
        ))
        
        fig_trend.update_layout(
            title="📈 Tendencia de Llamadas - Últimos 30 Días",
            xaxis_title="Fecha",
            yaxis_title="Número de Llamadas",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig_trend, use_container_width=True)
        
        # Insights automáticos
        st.markdown("### 💡 Insights Clave")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.success("✅ **Tendencia Positiva**: Las llamadas han aumentado 12.5% este mes")
            st.info("📅 **Mejor día**: Los martes tienen mayor volumen (+15%)")
        
        with col2:
            st.warning("⚠️ **Atención**: Tasa de atención bajó 2.1% esta semana")
            st.info("🕐 **Hora pico**: 10:00-11:00 AM concentra el 23% de llamadas")
    
    with tab_operativo:
        st.markdown("### ⚡ Monitoreo en Tiempo Real")
        
        # Métricas operativas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🔴 En curso", "12", "llamadas activas")
        with col2:
            st.metric("⏱️ Tiempo promedio", "3:45", "min por llamada")
        with col3:
            st.metric("👥 Agentes activos", "8/12", "disponibles")
        
        # Heatmap simplificado
        st.markdown("### 🗓️ Patrones por Hora y Día")
        
        # Crear heatmap de ejemplo
        import numpy as np
        
        dias = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
        horas = [f"{h:02d}:00" for h in range(8, 19)]
        
        # Datos sintéticos para el heatmap
        np.random.seed(42)
        data = np.random.randint(10, 100, size=(len(dias), len(horas)))
        
        fig_heatmap = go.Figure(data=go.Heatmap(
            z=data,
            x=horas,
            y=dias,
            colorscale='Blues',
            showscale=True
        ))
        
        fig_heatmap.update_layout(
            title="🔥 Mapa de Calor - Volumen de Llamadas",
            xaxis_title="Hora del Día",
            yaxis_title="Día de la Semana",
            height=400
        )
        
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    with tab_tecnico:
        st.markdown("### 🔬 Análisis Técnico Detallado")
        
        # Performance de modelos
        st.markdown("#### 🤖 Performance de Modelos IA")
        
        modelos_performance = pd.DataFrame({
            'Modelo': ['Random Forest', 'Gradient Boosting', 'Prophet', 'ARIMA'],
            'RMSE': [12.3, 11.8, 15.2, 18.7],
            'MAE': [9.1, 8.7, 11.3, 14.2],
            'R²': [0.94, 0.95, 0.89, 0.82]
        })
        
        fig_models = px.bar(
            modelos_performance, 
            x='Modelo', 
            y='R²',
            title="📊 Comparación de Modelos - R² Score",
            color='R²',
            color_continuous_scale='Viridis'
        )
        
        fig_models.update_layout(height=400)
        st.plotly_chart(fig_models, use_container_width=True)
        
        # Tabla detallada
        st.markdown("#### 📋 Métricas Detalladas")
        st.dataframe(modelos_performance, use_container_width=True)
        
        # Configuración técnica
        with st.expander("⚙️ Configuración Técnica"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                **Parámetros de Entrenamiento:**
                - Ventana temporal: 30 días
                - Validación cruzada: 5 folds
                - Métrica objetivo: RMSE
                """)
            
            with col2:
                st.markdown("""
                **Última actualización:**
                - Modelos: Hace 2 horas
                - Datos: Tiempo real
                - Performance: ✅ Óptima
                """)

def mostrar_alertas_inteligentes():
    """Sistema de alertas inteligentes y recomendaciones"""
    
    st.markdown("### 🚨 Alertas y Recomendaciones")
    
    # Alertas críticas
    alertas = [
        {
            "tipo": "warning",
            "icono": "⚠️",
            "titulo": "Pico de llamadas detectado",
            "mensaje": "El volumen actual (156 llamadas) está 23% por encima del promedio",
            "accion": "Considera activar más agentes",
            "prioridad": "alta"
        },
        {
            "tipo": "info",
            "icono": "💡",
            "titulo": "Oportunidad de optimización",
            "mensaje": "Los martes podrías reducir personal en horario 14:00-16:00",
            "accion": "Revisar programación de turnos",
            "prioridad": "media"
        },
        {
            "tipo": "success",
            "icono": "✅",
            "titulo": "Meta alcanzada",
            "mensaje": "Tasa de atención del 87% supera objetivo mensual",
            "accion": "Mantener estrategia actual",
            "prioridad": "baja"
        }
    ]
    
    for alerta in alertas:
        if alerta["tipo"] == "warning":
            st.warning(f"{alerta['icono']} **{alerta['titulo']}**\n\n{alerta['mensaje']}\n\n💡 *Recomendación: {alerta['accion']}*")
        elif alerta["tipo"] == "info":
            st.info(f"{alerta['icono']} **{alerta['titulo']}**\n\n{alerta['mensaje']}\n\n💡 *Recomendación: {alerta['accion']}*")
        elif alerta["tipo"] == "success":
            st.success(f"{alerta['icono']} **{alerta['titulo']}**\n\n{alerta['mensaje']}\n\n💡 *Recomendación: {alerta['accion']}*")

def mostrar_ayuda_contextual():
    """Sistema de ayuda contextual y tooltips"""
    
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 💡 Ayuda Contextual")
        
        # Ayuda basada en la página actual
        pagina_actual = st.session_state.get('pagina_activa', '🏠 Inicio')
        
        if pagina_actual == '🏠 Inicio':
            st.info("""
            **🏠 Estás en Inicio**
            
            Aquí puedes:
            - Ver el estado del pipeline
            - Cargar nuevos datos
            - Acceder a todas las funciones
            """)
        
        elif pagina_actual == '📊 Dashboard':
            st.info("""
            **📊 Estás en Dashboard**
            
            Visualiza:
            - Métricas principales
            - Gráficos temporales
            - Heatmaps de patrones
            """)
        
        elif pagina_actual == '🔧 Preparación de Datos':
            st.info("""
            **🔧 Preparación de Datos**
            
            Funciones:
            - Subir archivos CSV/Excel
            - Conectar API Reservo
            - Validar estructura
            """)
        
        # FAQ rápida
        with st.expander("❓ FAQ Rápida"):
            st.markdown("""
            **¿Qué formatos acepta?**
            CSV, Excel (.xlsx, .xls), JSON
            
            **¿Cuántos datos necesito?**
            Mínimo 30 días para buenas predicciones
            
            **¿Los datos están seguros?**
            Sí, todo se procesa localmente
            """)
        
        # Contacto soporte
        st.markdown("---")
        if st.button("📞 Contactar Soporte", use_container_width=True):
            st.balloons()
            st.success("¡Mensaje enviado! Te contactaremos pronto.")

# Función principal para implementar todas las mejoras UX
def aplicar_mejoras_ux():
    """Aplica todas las mejoras UX al dashboard"""
    
    # CSS personalizado para mejorar la apariencia
    st.markdown("""
    <style>
    /* Mejorar spacing y tipografía */
    .main > div {
        padding-top: 2rem;
    }
    
    /* Cards personalizadas */
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #4CAF50;
    }
    
    /* Botones mejorados */
    .stButton > button {
        border-radius: 10px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Alertas mejoradas */
    .stAlert {
        border-radius: 10px;
        border-left: 4px solid;
    }
    
    /* Navegación lateral */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    /* Títulos con mejor jerarquía */
    h1, h2, h3 {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 600;
        color: #2c3e50;
    }
    
    /* Progress bars mejoradas */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #4CAF50, #45a049);
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    return True

if __name__ == "__main__":
    st.set_page_config(
        page_title="CEAPSI UX - Improved",
        page_icon="🎨",
        layout="wide"
    )
    
    aplicar_mejoras_ux()
    
    st.title("🎨 CEAPSI - UX Mejorada")
    st.markdown("Prototipo de mejoras de experiencia de usuario")
    
    # Demostrar las mejoras
    objetivo = mostrar_onboarding_mejorado()
    
    if objetivo:
        st.success(f"Objetivo seleccionado: {objetivo}")
        
        mostrar_progreso_pipeline()
        mostrar_navegacion_contextual()
        mostrar_dashboard_mejorado()
        mostrar_alertas_inteligentes()
        mostrar_ayuda_contextual()