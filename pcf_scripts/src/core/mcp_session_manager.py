"""
CEAPSI - Gestor de Sesiones usando MCP Supabase
Maneja el guardado y recuperación de sesiones de análisis usando directamente MCP
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import uuid
import pickle
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class MCPSessionManager:
    """Gestor de sesiones usando MCP Supabase directamente"""
    
    def __init__(self):
        self.current_session_id = None
        self.current_user_id = None
        
        # Inicializar sesión en Streamlit
        if 'session_id' not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.analysis_results = {}
            st.session_state.uploaded_files = {}
            
        self.current_session_id = st.session_state.session_id
        
    def create_analysis_session(self, user_id: str, file_info: Dict, analysis_type: str = "call_prediction") -> str:
        """
        Crea una nueva sesión de análisis usando MCP
        
        Args:
            user_id: ID del usuario
            file_info: Información del archivo subido
            analysis_type: Tipo de análisis a realizar
            
        Returns:
            session_id: ID de la sesión creada
        """
        session_id = str(uuid.uuid4())
        
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'analysis_type': analysis_type,
            'file_info': json.dumps(file_info),  # MCP espera string JSON
            'status': 'created',
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(days=30)).isoformat(),
            'analysis_results': None,
            'results_summary': None
        }
        
        try:
            # Usar directamente st.connection con el MCP configurado
            if hasattr(st, 'connection'):
                # Intentar usar la conexión MCP si está disponible
                conn = st.connection('supabase', type='sql')
                
                # Insertar usando SQL directo compatible con MCP
                insert_query = """
                INSERT INTO analysis_sessions 
                (session_id, user_id, analysis_type, file_info, status, created_at, expires_at)
                VALUES (%s, %s, %s, %s::jsonb, %s, %s::timestamp, %s::timestamp)
                """
                
                conn.execute(insert_query, (
                    session_id,
                    user_id, 
                    analysis_type,
                    json.dumps(file_info),
                    'created',
                    session_data['created_at'],
                    session_data['expires_at']
                ))
                
                logger.info(f"Sesión {session_id} creada usando MCP")
                
            else:
                # Fallback: guardar en memoria local
                if 'mcp_sessions' not in st.session_state:
                    st.session_state.mcp_sessions = {}
                st.session_state.mcp_sessions[session_id] = session_data
                logger.info(f"Sesión {session_id} guardada localmente (MCP no disponible)")
        
        except Exception as e:
            logger.error(f"Error creando sesión con MCP: {e}")
            # Fallback: guardar en memoria local
            if 'mcp_sessions' not in st.session_state:
                st.session_state.mcp_sessions = {}
            st.session_state.mcp_sessions[session_id] = session_data
        
        # Guardar en sesión local como backup
        st.session_state.session_id = session_id
        st.session_state.session_data = session_data
        
        return session_id
    
    def save_analysis_results(self, session_id: str, results: Dict) -> bool:
        """
        Guarda los resultados del análisis usando MCP
        
        Args:
            session_id: ID de la sesión
            results: Diccionario con resultados del análisis
            
        Returns:
            bool: True si se guardó correctamente
        """
        try:
            # Serializar resultados para almacenamiento
            serialized_results = self._serialize_results(results)
            results_summary = self._generate_summary(results)
            
            # Preparar datos para actualización
            update_data = {
                'analysis_results': json.dumps(serialized_results),
                'results_summary': json.dumps(results_summary),
                'status': 'completed',
                'completed_at': datetime.now().isoformat()
            }
            
            try:
                if hasattr(st, 'connection'):
                    # Usar MCP para actualizar
                    conn = st.connection('supabase', type='sql')
                    
                    update_query = """
                    UPDATE analysis_sessions 
                    SET analysis_results = %s::jsonb,
                        results_summary = %s::jsonb,
                        status = %s,
                        completed_at = %s::timestamp
                    WHERE session_id = %s
                    """
                    
                    conn.execute(update_query, (
                        update_data['analysis_results'],
                        update_data['results_summary'],
                        update_data['status'],
                        update_data['completed_at'],
                        session_id
                    ))
                    
                    logger.info(f"Resultados guardados para sesión {session_id} usando MCP")
                    return True
                
                else:
                    # Fallback: actualizar en memoria local
                    if 'mcp_sessions' in st.session_state and session_id in st.session_state.mcp_sessions:
                        st.session_state.mcp_sessions[session_id].update(update_data)
                        return True
                    
            except Exception as e:
                logger.error(f"Error usando MCP para guardar: {e}")
                # Fallback: guardar localmente
                if 'mcp_sessions' not in st.session_state:
                    st.session_state.mcp_sessions = {}
                if session_id not in st.session_state.mcp_sessions:
                    st.session_state.mcp_sessions[session_id] = {'session_id': session_id}
                st.session_state.mcp_sessions[session_id].update(update_data)
                return True
            
            # Guardar en sesión local como respaldo
            if 'analysis_results' not in st.session_state:
                st.session_state.analysis_results = {}
            st.session_state.analysis_results[session_id] = update_data
            
            return True
            
        except Exception as e:
            logger.error(f"Error guardando resultados: {e}")
            return False
    
    def load_analysis_session(self, session_id: str) -> Optional[Dict]:
        """
        Carga una sesión de análisis usando MCP
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Dict con datos de la sesión o None si no existe
        """
        try:
            if hasattr(st, 'connection'):
                # Usar MCP para cargar
                conn = st.connection('supabase', type='sql')
                
                select_query = """
                SELECT * FROM analysis_sessions 
                WHERE session_id = %s
                """
                
                result = conn.query(select_query, params=[session_id])
                
                if not result.empty:
                    session_data = result.iloc[0].to_dict()
                    
                    # Deserializar resultados si existen
                    if session_data.get('analysis_results'):
                        try:
                            if isinstance(session_data['analysis_results'], str):
                                results_data = json.loads(session_data['analysis_results'])
                            else:
                                results_data = session_data['analysis_results']
                            session_data['analysis_results'] = self._deserialize_results(results_data)
                        except Exception as e:
                            logger.error(f"Error deserializando resultados: {e}")
                    
                    # Deserializar file_info si es string
                    if isinstance(session_data.get('file_info'), str):
                        try:
                            session_data['file_info'] = json.loads(session_data['file_info'])
                        except:
                            pass
                    
                    return session_data
            
            # Fallback: cargar desde memoria local
            if hasattr(st.session_state, 'mcp_sessions') and session_id in st.session_state.mcp_sessions:
                return st.session_state.mcp_sessions[session_id]
            
            # Cargar desde session state backup
            if hasattr(st.session_state, 'analysis_results') and session_id in st.session_state.analysis_results:
                return st.session_state.analysis_results[session_id]
                
        except Exception as e:
            logger.error(f"Error cargando sesión: {e}")
            
        return None
    
    def list_user_sessions(self, user_id: str, limit: int = 50) -> List[Dict]:
        """
        Lista las sesiones de un usuario usando MCP
        
        Args:
            user_id: ID del usuario
            limit: Número máximo de sesiones a retornar
            
        Returns:
            Lista de sesiones del usuario
        """
        try:
            if hasattr(st, 'connection'):
                # Usar MCP para listar
                conn = st.connection('supabase', type='sql')
                
                select_query = """
                SELECT session_id, analysis_type, status, created_at, completed_at, 
                       results_summary, file_info
                FROM analysis_sessions 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
                """
                
                result = conn.query(select_query, params=[user_id, limit])
                
                if not result.empty:
                    sessions = []
                    for _, row in result.iterrows():
                        session_dict = row.to_dict()
                        
                        # Parsear JSON strings si es necesario
                        for json_field in ['results_summary', 'file_info']:
                            if isinstance(session_dict.get(json_field), str):
                                try:
                                    session_dict[json_field] = json.loads(session_dict[json_field])
                                except:
                                    pass
                        
                        sessions.append(session_dict)
                    
                    return sessions
            
            # Fallback: cargar desde memoria local
            if hasattr(st.session_state, 'mcp_sessions'):
                user_sessions = []
                for session_id, session_data in st.session_state.mcp_sessions.items():
                    if session_data.get('user_id') == user_id:
                        user_sessions.append(session_data)
                
                # Ordenar por fecha de creación
                user_sessions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
                return user_sessions[:limit]
            
            return []
            
        except Exception as e:
            logger.error(f"Error listando sesiones: {e}")
            return []
    
    def delete_session(self, session_id: str) -> bool:
        """
        Elimina una sesión de análisis usando MCP
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            bool: True si se eliminó correctamente
        """
        try:
            if hasattr(st, 'connection'):
                # Usar MCP para eliminar
                conn = st.connection('supabase', type='sql')
                
                delete_query = """
                DELETE FROM analysis_sessions 
                WHERE session_id = %s
                """
                
                conn.execute(delete_query, [session_id])
                logger.info(f"Sesión {session_id} eliminada usando MCP")
                return True
            
            # Fallback: eliminar de memoria local
            if hasattr(st.session_state, 'mcp_sessions') and session_id in st.session_state.mcp_sessions:
                del st.session_state.mcp_sessions[session_id]
            
            # Eliminar de session state backup
            if hasattr(st.session_state, 'analysis_results') and session_id in st.session_state.analysis_results:
                del st.session_state.analysis_results[session_id]
                
            return True
            
        except Exception as e:
            logger.error(f"Error eliminando sesión: {e}")
            return False
    
    def _serialize_results(self, results: Dict) -> Dict:
        """Serializa resultados complejos para almacenamiento en MCP"""
        serialized = {}
        
        for key, value in results.items():
            if isinstance(value, pd.DataFrame):
                # Convertir DataFrame a JSON
                serialized[key] = {
                    'type': 'dataframe',
                    'data': value.to_json(orient='records', date_format='iso'),
                    'columns': list(value.columns),
                    'shape': list(value.shape)
                }
            elif isinstance(value, np.ndarray):
                # Convertir array numpy a lista
                serialized[key] = {
                    'type': 'numpy_array',
                    'data': value.tolist(),
                    'shape': list(value.shape),
                    'dtype': str(value.dtype)
                }
            elif isinstance(value, (dict, list, str, int, float, bool)) or value is None:
                # Tipos básicos JSON
                serialized[key] = value
            else:
                # Otros objetos - usar pickle + base64
                try:
                    pickled = pickle.dumps(value)
                    encoded = base64.b64encode(pickled).decode('utf-8')
                    serialized[key] = {
                        'type': 'pickled',
                        'data': encoded
                    }
                except Exception as e:
                    logger.warning(f"No se pudo serializar {key}: {e}")
                    serialized[key] = str(value)
        
        return serialized
    
    def _deserialize_results(self, serialized: Dict) -> Dict:
        """Deserializa resultados desde almacenamiento MCP"""
        results = {}
        
        for key, value in serialized.items():
            if isinstance(value, dict) and 'type' in value:
                if value['type'] == 'dataframe':
                    # Reconstruir DataFrame
                    try:
                        df = pd.read_json(value['data'], orient='records')
                        results[key] = df
                    except Exception as e:
                        logger.warning(f"Error deserializando DataFrame {key}: {e}")
                        results[key] = value
                elif value['type'] == 'numpy_array':
                    # Reconstruir array numpy
                    try:
                        arr = np.array(value['data'])
                        if 'shape' in value:
                            arr = arr.reshape(value['shape'])
                        results[key] = arr
                    except Exception as e:
                        logger.warning(f"Error deserializando array {key}: {e}")
                        results[key] = value
                elif value['type'] == 'pickled':
                    # Deserializar objeto pickle
                    try:
                        decoded = base64.b64decode(value['data'])
                        results[key] = pickle.loads(decoded)
                    except Exception as e:
                        logger.warning(f"No se pudo deserializar {key}: {e}")
                        results[key] = value['data']
                else:
                    results[key] = value
            else:
                results[key] = value
        
        return results
    
    def _generate_summary(self, results: Dict) -> Dict:
        """Genera un resumen de los resultados para almacenamiento eficiente en MCP"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_keys': len(results),
            'has_predictions': False,
            'has_models': False,
            'prediction_period': None,
            'model_metrics': {}
        }
        
        # Analizar contenido
        for key, value in results.items():
            if 'prediction' in key.lower():
                summary['has_predictions'] = True
                if isinstance(value, pd.DataFrame) and 'ds' in value.columns:
                    dates = pd.to_datetime(value['ds'])
                    summary['prediction_period'] = {
                        'start': dates.min().isoformat(),
                        'end': dates.max().isoformat(),
                        'days': len(dates)
                    }
            
            if 'model' in key.lower() or 'mae' in key.lower() or 'rmse' in key.lower():
                summary['has_models'] = True
                if isinstance(value, (int, float)):
                    summary['model_metrics'][key] = float(value)  # Asegurar JSON serializable
        
        return summary

def get_mcp_session_manager() -> MCPSessionManager:
    """Obtiene la instancia global del gestor de sesiones MCP"""
    if 'mcp_session_manager' not in st.session_state:
        st.session_state.mcp_session_manager = MCPSessionManager()
    return st.session_state.mcp_session_manager