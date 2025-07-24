"""
CEAPSI - Frontend Optimizado
Mejoras de performance y UX para la aplicación principal
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger('CEAPSI_FRONTEND_OPT')

class OptimizedFrontend:
    """Clase para manejar componentes frontend optimizados"""
    
    def __init__(self):
        self.plotly_config = {
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': [
                'zoom2d', 'pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d',
                'autoScale2d', 'resetScale2d', 'hoverClosestCartesian', 'hoverCompareCartesian',
                'zoom3d', 'pan3d', 'resetCameraDefault3d', 'resetCameraLastSave3d',
                'hoverClosest3d', 'orbitRotation', 'tableRotation'
            ],
            'modeBarButtonsToAdd': ['drawline', 'drawopenpath', 'drawclosedpath', 'drawcircle', 'drawrect', 'eraseshape'],
            'toImageButtonOptions': {
                'format': 'png',
                'filename': 'ceapsi_chart',
                'height': 500,
                'width': 700,
                'scale': 1
            },
            'responsive': True
        }
    
    @staticmethod
    @st.cache_data(ttl=300)
    def create_optimized_chart(
        data: Dict[str, Any], 
        chart_type: str = "line",
        title: str = "",
        height: int = 400,
        show_legend: bool = True
    ) -> go.Figure:
        """Crear gráfico optimizado con configuración estándar"""
        
        fig = None
        
        if chart_type == "line":
            fig = go.Figure()
            for series_name, series_data in data.items():
                fig.add_trace(go.Scatter(
                    x=series_data.get('x', []),
                    y=series_data.get('y', []),
                    mode='lines+markers',
                    name=series_name,
                    line=dict(width=2),
                    marker=dict(size=6)
                ))
        
        elif chart_type == "bar":
            fig = go.Figure()
            for series_name, series_data in data.items():
                fig.add_trace(go.Bar(
                    x=series_data.get('x', []),
                    y=series_data.get('y', []),
                    name=series_name,
                    marker_color=series_data.get('color', '#1f77b4')
                ))
        
        elif chart_type == "pie":
            fig = go.Figure(data=[
                go.Pie(
                    labels=data.get('labels', []),
                    values=data.get('values', []),
                    hole=0.3,
                    textinfo='label+percent',
                    textposition='auto'
                )
            ])
        
        elif chart_type == "heatmap":
            fig = go.Figure(data=go.Heatmap(
                z=data.get('z', []),
                x=data.get('x', []),
                y=data.get('y', []),
                colorscale='Viridis',
                showscale=True
            ))
        
        # Configuración común optimizada
        if fig:
            fig.update_layout(
                title={
                    'text': title,
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 16, 'family': 'Arial, sans-serif'}
                },
                height=height,
                showlegend=show_legend,
                margin=dict(l=50, r=50, t=50, b=50),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Arial, sans-serif", size=12),
                hovermode='x unified' if chart_type == 'line' else 'closest',
                # Responsive design
                autosize=True,
                # Performance optimizations
                uirevision='constant'  # Prevent unnecessary re-renders
            )
            
            # Grid styling
            if chart_type in ['line', 'bar']:
                fig.update_xaxes(
                    gridcolor='rgba(128,128,128,0.2)',
                    gridwidth=1,
                    zeroline=False
                )
                fig.update_yaxes(
                    gridcolor='rgba(128,128,128,0.2)',
                    gridwidth=1,
                    zeroline=False
                )
        
        return fig
    
    def render_chart(self, fig: go.Figure, key: str = None) -> None:
        """Renderizar gráfico con configuración optimizada"""
        st.plotly_chart(
            fig,
            use_container_width=True,
            config=self.plotly_config,
            key=key,
            theme="streamlit"
        )
    
    @staticmethod
    def create_metric_cards(metrics: Dict[str, Dict[str, Any]], columns: int = 4) -> None:
        """Crear tarjetas de métricas optimizadas"""
        cols = st.columns(columns)
        
        for i, (metric_name, metric_data) in enumerate(metrics.items()):
            with cols[i % columns]:
                value = metric_data.get('value', 0)
                delta = metric_data.get('delta', None)
                delta_color = metric_data.get('delta_color', 'normal')
                
                st.metric(
                    label=metric_name,
                    value=value,
                    delta=delta,
                    delta_color=delta_color
                )
    
    @staticmethod
    def create_status_indicator(status: str, message: str = "") -> None:
        """Crear indicador de estado optimizado"""
        status_config = {
            'success': ('✅', 'success', '#28a745'),
            'warning': ('⚠️', 'warning', '#ffc107'),
            'error': ('❌', 'error', '#dc3545'),
            'info': ('ℹ️', 'info', '#17a2b8'),
            'loading': ('⏳', 'info', '#6c757d')
        }
        
        if status in status_config:
            icon, level, color = status_config[status]
            
            # Usar el método de Streamlit apropiado
            if level == 'success':
                st.success(f"{icon} {message}")
            elif level == 'warning':
                st.warning(f"{icon} {message}")
            elif level == 'error':
                st.error(f"{icon} {message}")
            else:
                st.info(f"{icon} {message}")
    
    @staticmethod 
    def create_collapsible_section(title: str, content_func, expanded: bool = False) -> None:
        """Crear sección colapsable optimizada"""
        with st.expander(title, expanded=expanded):
            content_func()
    
    @staticmethod
    def create_loading_placeholder(message: str = "Procesando...") -> None:
        """Crear placeholder de carga optimizado"""
        placeholder = st.empty()
        
        with placeholder.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown(f"""
                <div style="text-align: center; padding: 2rem;">
                    <div style="font-size: 2rem; margin-bottom: 1rem;">⏳</div>
                    <div style="font-size: 1.2rem; color: #666;">{message}</div>
                </div>
                """, unsafe_allow_html=True)
        
        return placeholder
    
    @staticmethod
    def optimize_dataframe_display(df, max_rows: int = 1000) -> None:
        """Mostrar DataFrame optimizado para performance"""
        if len(df) > max_rows:
            st.warning(f"⚠️ Mostrando primeros {max_rows} registros de {len(df)} totales")
            st.dataframe(
                df.head(max_rows),
                use_container_width=True,
                height=400
            )
        else:
            st.dataframe(
                df,
                use_container_width=True,
                height=min(400, len(df) * 35 + 50)
            )
    
    @staticmethod
    def create_navigation_breadcrumb(pages: list, current_page: str) -> None:
        """Crear breadcrumb de navegación"""
        breadcrumb_html = []
        
        for i, page in enumerate(pages):
            if page == current_page:
                breadcrumb_html.append(f'<span style="font-weight: bold; color: #1f77b4;">{page}</span>')
            else:
                breadcrumb_html.append(f'<span style="color: #666;">{page}</span>')
            
            if i < len(pages) - 1:
                breadcrumb_html.append('<span style="color: #ccc; margin: 0 8px;">›</span>')
        
        st.markdown(
            f'<div style="margin-bottom: 1rem; font-size: 0.9rem;">{"".join(breadcrumb_html)}</div>',
            unsafe_allow_html=True
        )

class LazyLoader:
    """Cargador lazy para módulos pesados"""
    
    def __init__(self):
        self._modules = {}
    
    def load_module(self, module_name: str, import_path: str):
        """Cargar módulo bajo demanda"""
        if module_name not in self._modules:
            try:
                module = __import__(import_path, fromlist=[''])
                self._modules[module_name] = module
                logger.info(f"Módulo {module_name} cargado exitosamente")
            except ImportError as e:
                logger.error(f"Error cargando módulo {module_name}: {e}")
                self._modules[module_name] = None
        
        return self._modules[module_name]
    
    def is_module_loaded(self, module_name: str) -> bool:
        """Verificar si un módulo está cargado"""
        return module_name in self._modules and self._modules[module_name] is not None

# Instancia global
optimized_frontend = OptimizedFrontend()
lazy_loader = LazyLoader()

# Funciones helper para uso directo
def create_chart(data, chart_type="line", title="", height=400):
    """Helper para crear gráficos optimizados"""
    return optimized_frontend.create_optimized_chart(data, chart_type, title, height)

def render_chart(fig, key=None):
    """Helper para renderizar gráficos optimizados"""
    optimized_frontend.render_chart(fig, key)

def show_metrics(metrics, columns=4):
    """Helper para mostrar métricas"""
    optimized_frontend.create_metric_cards(metrics, columns)

def show_status(status, message=""):
    """Helper para mostrar estado"""
    optimized_frontend.create_status_indicator(status, message)