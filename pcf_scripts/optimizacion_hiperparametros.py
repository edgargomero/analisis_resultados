#!/usr/bin/env python3
"""
Optimización Avanzada de Hiperparámetros para Análisis de Llamadas
Sistema completo de tuning automático para modelos de predicción
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import pickle
from pathlib import Path
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Any, Optional
import warnings
warnings.filterwarnings('ignore')

# ML Libraries
from sklearn.model_selection import (
    GridSearchCV, RandomizedSearchCV, TimeSeriesSplit,
    cross_val_score, validation_curve
)
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.feature_selection import SelectKBest, f_regression, RFE

# Optimization Libraries
try:
    from skopt import BayesSearchCV
    from skopt.space import Real, Integer, Categorical
    BAYESIAN_AVAILABLE = True
except ImportError:
    BAYESIAN_AVAILABLE = False
    
try:
    import optuna
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False

# Time Series Libraries
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    ARIMA_AVAILABLE = True
except ImportError:
    ARIMA_AVAILABLE = False

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizadorHiperparametros:
    """Optimizador avanzado de hiperparámetros para modelos de predicción de llamadas"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.absolute()
        self.resultados_path = self.base_path / "resultados_tuning"
        self.resultados_path.mkdir(exist_ok=True)
        
        # Espacios de búsqueda para diferentes modelos
        self.espacios_busqueda = self._definir_espacios_busqueda()
        
        # Configuraciones de optimización
        self.configuraciones_opt = {
            'grid_search': {
                'cv': 5,
                'scoring': 'neg_mean_squared_error',
                'n_jobs': -1,
                'verbose': 1
            },
            'random_search': {
                'n_iter': 100,
                'cv': 5,
                'scoring': 'neg_mean_squared_error',
                'n_jobs': -1,
                'random_state': 42
            },
            'bayesian_search': {
                'n_iter': 50,
                'cv': 5,
                'scoring': 'neg_mean_squared_error',
                'n_jobs': -1,
                'random_state': 42
            }
        }
        
        # Métricas de evaluación
        self.metricas = {
            'rmse': lambda y_true, y_pred: np.sqrt(mean_squared_error(y_true, y_pred)),
            'mae': mean_absolute_error,
            'r2': r2_score,
            'mape': lambda y_true, y_pred: np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        }
    
    def _definir_espacios_busqueda(self) -> Dict[str, Dict]:
        """Define los espacios de búsqueda para cada modelo"""
        
        espacios = {
            'RandomForest': {
                'grid': {
                    'n_estimators': [50, 100, 200, 300],
                    'max_depth': [5, 10, 15, 20, None],
                    'min_samples_split': [2, 5, 10],
                    'min_samples_leaf': [1, 2, 4],
                    'max_features': ['sqrt', 'log2', None]
                },
                'random': {
                    'n_estimators': [10, 50, 100, 200, 300, 500],
                    'max_depth': [3, 5, 10, 15, 20, 25, None],
                    'min_samples_split': [2, 5, 10, 15, 20],
                    'min_samples_leaf': [1, 2, 4, 6, 8],
                    'max_features': ['sqrt', 'log2', None],
                    'bootstrap': [True, False]
                }
            },
            
            'GradientBoosting': {
                'grid': {
                    'n_estimators': [50, 100, 200],
                    'learning_rate': [0.01, 0.1, 0.2],
                    'max_depth': [3, 5, 7],
                    'subsample': [0.8, 0.9, 1.0]
                },
                'random': {
                    'n_estimators': [50, 100, 150, 200, 300],
                    'learning_rate': [0.01, 0.05, 0.1, 0.15, 0.2],
                    'max_depth': [3, 4, 5, 6, 7, 8],
                    'subsample': [0.7, 0.8, 0.9, 1.0],
                    'min_samples_split': [2, 5, 10],
                    'min_samples_leaf': [1, 2, 4]
                }
            },
            
            'SVR': {
                'grid': {
                    'C': [0.1, 1, 10, 100],
                    'gamma': ['scale', 'auto', 0.001, 0.01, 0.1, 1],
                    'kernel': ['rbf', 'linear', 'poly']
                },
                'random': {
                    'C': [0.01, 0.1, 1, 10, 100, 1000],
                    'gamma': ['scale', 'auto', 0.0001, 0.001, 0.01, 0.1, 1],
                    'kernel': ['rbf', 'linear', 'poly', 'sigmoid'],
                    'epsilon': [0.01, 0.1, 0.2, 0.5]
                }
            },
            
            'Ridge': {
                'grid': {
                    'alpha': [0.1, 1.0, 10.0, 100.0],
                    'solver': ['auto', 'svd', 'cholesky', 'lsqr']
                },
                'random': {
                    'alpha': np.logspace(-4, 4, 50),
                    'solver': ['auto', 'svd', 'cholesky', 'lsqr', 'sparse_cg', 'sag', 'saga']
                }
            },
            
            'Lasso': {
                'grid': {
                    'alpha': [0.001, 0.01, 0.1, 1.0, 10.0],
                    'max_iter': [1000, 2000, 3000]
                },
                'random': {
                    'alpha': np.logspace(-4, 2, 50),
                    'max_iter': [500, 1000, 2000, 3000, 5000],
                    'selection': ['cyclic', 'random']
                }
            },
            
            'ElasticNet': {
                'grid': {
                    'alpha': [0.001, 0.01, 0.1, 1.0],
                    'l1_ratio': [0.1, 0.3, 0.5, 0.7, 0.9]
                },
                'random': {
                    'alpha': np.logspace(-4, 2, 30),
                    'l1_ratio': np.linspace(0.1, 0.9, 20),
                    'max_iter': [500, 1000, 2000, 3000]
                }
            },
            
            'KNN': {
                'grid': {
                    'n_neighbors': [3, 5, 7, 9, 11],
                    'weights': ['uniform', 'distance'],
                    'metric': ['euclidean', 'manhattan']
                },
                'random': {
                    'n_neighbors': list(range(3, 31)),
                    'weights': ['uniform', 'distance'],
                    'metric': ['euclidean', 'manhattan', 'minkowski'],
                    'leaf_size': [10, 20, 30, 40, 50]
                }
            },
            
            'MLP': {
                'grid': {
                    'hidden_layer_sizes': [(50,), (100,), (50, 50), (100, 50)],
                    'activation': ['relu', 'tanh'],
                    'alpha': [0.0001, 0.001, 0.01],
                    'learning_rate': ['constant', 'adaptive']
                },
                'random': {
                    'hidden_layer_sizes': [(50,), (100,), (150,), (50, 50), (100, 50), (100, 100), (150, 100, 50)],
                    'activation': ['relu', 'tanh', 'logistic'],
                    'alpha': np.logspace(-5, 1, 20),
                    'learning_rate': ['constant', 'invscaling', 'adaptive'],
                    'learning_rate_init': [0.001, 0.01, 0.1],
                    'max_iter': [200, 300, 500, 1000]
                }
            }
        }
        
        # Agregar espacios bayesianos si está disponible
        if BAYESIAN_AVAILABLE:
            espacios['RandomForest']['bayesian'] = {
                'n_estimators': Integer(10, 500),
                'max_depth': Integer(3, 30),
                'min_samples_split': Integer(2, 20),
                'min_samples_leaf': Integer(1, 10),
                'max_features': Categorical(['sqrt', 'log2', None])
            }
            
            espacios['GradientBoosting']['bayesian'] = {
                'n_estimators': Integer(50, 300),
                'learning_rate': Real(0.01, 0.3, prior='log-uniform'),
                'max_depth': Integer(3, 10),
                'subsample': Real(0.6, 1.0)
            }
            
            espacios['SVR']['bayesian'] = {
                'C': Real(0.01, 1000, prior='log-uniform'),
                'gamma': Real(0.0001, 1, prior='log-uniform'),
                'kernel': Categorical(['rbf', 'linear', 'poly']),
                'epsilon': Real(0.01, 1.0)
            }
        
        return espacios
    
    def _obtener_modelo(self, nombre_modelo: str, **params):
        """Obtiene una instancia del modelo con los parámetros especificados"""
        
        modelos = {
            'RandomForest': RandomForestRegressor,
            'GradientBoosting': GradientBoostingRegressor,
            'SVR': SVR,
            'Ridge': Ridge,
            'Lasso': Lasso,
            'ElasticNet': ElasticNet,
            'KNN': KNeighborsRegressor,
            'DecisionTree': DecisionTreeRegressor,
            'MLP': MLPRegressor,
            'LinearRegression': LinearRegression
        }
        
        if nombre_modelo not in modelos:
            raise ValueError(f"Modelo no soportado: {nombre_modelo}")
        
        # Parámetros por defecto para algunos modelos
        params_default = {
            'RandomForest': {'random_state': 42, 'n_jobs': -1},
            'GradientBoosting': {'random_state': 42},
            'MLP': {'random_state': 42, 'max_iter': 500},
            'DecisionTree': {'random_state': 42}
        }
        
        if nombre_modelo in params_default:
            final_params = {**params_default[nombre_modelo], **params}
        else:
            final_params = params
        
        return modelos[nombre_modelo](**final_params)
    
    def optimizar_grid_search(self, X: pd.DataFrame, y: pd.Series, 
                             nombre_modelo: str, cv_folds: int = 5) -> Dict:
        """Optimización usando Grid Search"""
        
        logger.info(f"Iniciando Grid Search para {nombre_modelo}")
        
        if nombre_modelo not in self.espacios_busqueda:
            raise ValueError(f"Espacio de búsqueda no definido para {nombre_modelo}")
        
        modelo_base = self._obtener_modelo(nombre_modelo)
        param_grid = self.espacios_busqueda[nombre_modelo]['grid']
        
        # Configurar validación cruzada para series de tiempo
        if len(X) > 100:
            cv = TimeSeriesSplit(n_splits=cv_folds)
        else:
            cv = cv_folds
        
        grid_search = GridSearchCV(
            estimator=modelo_base,
            param_grid=param_grid,
            cv=cv,
            **self.configuraciones_opt['grid_search']
        )
        
        start_time = datetime.now()
        grid_search.fit(X, y)
        tiempo_total = (datetime.now() - start_time).total_seconds()
        
        # Evaluar mejor modelo
        mejor_modelo = grid_search.best_estimator_
        evaluacion = self._evaluar_modelo(mejor_modelo, X, y, cv)
        
        resultados = {
            'metodo': 'Grid Search',
            'modelo': nombre_modelo,
            'mejores_parametros': grid_search.best_params_,
            'mejor_score': grid_search.best_score_,
            'evaluacion': evaluacion,
            'tiempo_entrenamiento': tiempo_total,
            'n_combinaciones': len(grid_search.cv_results_['params']),
            'modelo_entrenado': mejor_modelo,
            'cv_results': grid_search.cv_results_
        }
        
        logger.info(f"Grid Search completado en {tiempo_total:.2f}s")
        return resultados
    
    def optimizar_random_search(self, X: pd.DataFrame, y: pd.Series, 
                               nombre_modelo: str, n_iter: int = 100, 
                               cv_folds: int = 5) -> Dict:
        """Optimización usando Random Search"""
        
        logger.info(f"Iniciando Random Search para {nombre_modelo}")
        
        if nombre_modelo not in self.espacios_busqueda:
            raise ValueError(f"Espacio de búsqueda no definido para {nombre_modelo}")
        
        modelo_base = self._obtener_modelo(nombre_modelo)
        param_distributions = self.espacios_busqueda[nombre_modelo]['random']
        
        # Configurar validación cruzada
        if len(X) > 100:
            cv = TimeSeriesSplit(n_splits=cv_folds)
        else:
            cv = cv_folds
        
        random_search = RandomizedSearchCV(
            estimator=modelo_base,
            param_distributions=param_distributions,
            n_iter=n_iter,
            cv=cv,
            **self.configuraciones_opt['random_search']
        )
        
        start_time = datetime.now()
        random_search.fit(X, y)
        tiempo_total = (datetime.now() - start_time).total_seconds()
        
        # Evaluar mejor modelo
        mejor_modelo = random_search.best_estimator_
        evaluacion = self._evaluar_modelo(mejor_modelo, X, y, cv)
        
        resultados = {
            'metodo': 'Random Search',
            'modelo': nombre_modelo,
            'mejores_parametros': random_search.best_params_,
            'mejor_score': random_search.best_score_,
            'evaluacion': evaluacion,
            'tiempo_entrenamiento': tiempo_total,
            'n_iteraciones': n_iter,
            'modelo_entrenado': mejor_modelo,
            'cv_results': random_search.cv_results_
        }
        
        logger.info(f"Random Search completado en {tiempo_total:.2f}s")
        return resultados
    
    def optimizar_bayesian_search(self, X: pd.DataFrame, y: pd.Series, 
                                 nombre_modelo: str, n_iter: int = 50, 
                                 cv_folds: int = 5) -> Dict:
        """Optimización usando Bayesian Search (requiere scikit-optimize)"""
        
        if not BAYESIAN_AVAILABLE:
            raise ImportError("scikit-optimize no está disponible. Instala con: pip install scikit-optimize")
        
        logger.info(f"Iniciando Bayesian Search para {nombre_modelo}")
        
        if nombre_modelo not in self.espacios_busqueda or 'bayesian' not in self.espacios_busqueda[nombre_modelo]:
            raise ValueError(f"Espacio bayesiano no definido para {nombre_modelo}")
        
        modelo_base = self._obtener_modelo(nombre_modelo)
        search_spaces = self.espacios_busqueda[nombre_modelo]['bayesian']
        
        # Configurar validación cruzada
        if len(X) > 100:
            cv = TimeSeriesSplit(n_splits=cv_folds)
        else:
            cv = cv_folds
        
        bayes_search = BayesSearchCV(
            estimator=modelo_base,
            search_spaces=search_spaces,
            n_iter=n_iter,
            cv=cv,
            **self.configuraciones_opt['bayesian_search']
        )
        
        start_time = datetime.now()
        bayes_search.fit(X, y)
        tiempo_total = (datetime.now() - start_time).total_seconds()
        
        # Evaluar mejor modelo
        mejor_modelo = bayes_search.best_estimator_
        evaluacion = self._evaluar_modelo(mejor_modelo, X, y, cv)
        
        resultados = {
            'metodo': 'Bayesian Search',
            'modelo': nombre_modelo,
            'mejores_parametros': bayes_search.best_params_,
            'mejor_score': bayes_search.best_score_,
            'evaluacion': evaluacion,
            'tiempo_entrenamiento': tiempo_total,
            'n_iteraciones': n_iter,
            'modelo_entrenado': mejor_modelo,
            'cv_results': bayes_search.cv_results_
        }
        
        logger.info(f"Bayesian Search completado en {tiempo_total:.2f}s")
        return resultados
    
    def optimizar_optuna(self, X: pd.DataFrame, y: pd.Series, 
                        nombre_modelo: str, n_trials: int = 100, 
                        cv_folds: int = 5) -> Dict:
        """Optimización usando Optuna"""
        
        if not OPTUNA_AVAILABLE:
            raise ImportError("Optuna no está disponible. Instala con: pip install optuna")
        
        logger.info(f"Iniciando optimización Optuna para {nombre_modelo}")
        
        def objective(trial):
            # Definir hiperparámetros según el modelo
            if nombre_modelo == 'RandomForest':
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 10, 500),
                    'max_depth': trial.suggest_int('max_depth', 3, 30),
                    'min_samples_split': trial.suggest_int('min_samples_split', 2, 20),
                    'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 10),
                    'max_features': trial.suggest_categorical('max_features', ['sqrt', 'log2', None])
                }
            elif nombre_modelo == 'GradientBoosting':
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                    'max_depth': trial.suggest_int('max_depth', 3, 10),
                    'subsample': trial.suggest_float('subsample', 0.6, 1.0)
                }
            elif nombre_modelo == 'SVR':
                params = {
                    'C': trial.suggest_float('C', 0.01, 1000, log=True),
                    'gamma': trial.suggest_float('gamma', 0.0001, 1, log=True),
                    'kernel': trial.suggest_categorical('kernel', ['rbf', 'linear', 'poly']),
                    'epsilon': trial.suggest_float('epsilon', 0.01, 1.0)
                }
            else:
                raise ValueError(f"Modelo {nombre_modelo} no configurado para Optuna")
            
            modelo = self._obtener_modelo(nombre_modelo, **params)
            
            # Validación cruzada
            if len(X) > 100:
                cv = TimeSeriesSplit(n_splits=cv_folds)
            else:
                cv = cv_folds
            
            scores = cross_val_score(modelo, X, y, cv=cv, 
                                   scoring='neg_mean_squared_error', n_jobs=-1)
            return scores.mean()
        
        # Crear estudio Optuna
        study = optuna.create_study(direction='maximize')
        
        start_time = datetime.now()
        study.optimize(objective, n_trials=n_trials)
        tiempo_total = (datetime.now() - start_time).total_seconds()
        
        # Entrenar modelo con mejores parámetros
        mejor_modelo = self._obtener_modelo(nombre_modelo, **study.best_params)
        mejor_modelo.fit(X, y)
        
        # Evaluar modelo
        if len(X) > 100:
            cv = TimeSeriesSplit(n_splits=cv_folds)
        else:
            cv = cv_folds
        evaluacion = self._evaluar_modelo(mejor_modelo, X, y, cv)
        
        resultados = {
            'metodo': 'Optuna',
            'modelo': nombre_modelo,
            'mejores_parametros': study.best_params,
            'mejor_score': study.best_value,
            'evaluacion': evaluacion,
            'tiempo_entrenamiento': tiempo_total,
            'n_trials': n_trials,
            'modelo_entrenado': mejor_modelo,
            'estudio_optuna': study
        }
        
        logger.info(f"Optuna completado en {tiempo_total:.2f}s")
        return resultados
    
    def _evaluar_modelo(self, modelo, X: pd.DataFrame, y: pd.Series, cv) -> Dict:
        """Evalúa un modelo usando múltiples métricas"""
        
        # Predicciones con validación cruzada
        from sklearn.model_selection import cross_val_predict
        y_pred_cv = cross_val_predict(modelo, X, y, cv=cv)
        
        # Calcular métricas
        evaluacion = {}
        for nombre_metrica, funcion_metrica in self.metricas.items():
            try:
                valor = funcion_metrica(y, y_pred_cv)
                evaluacion[nombre_metrica] = valor
            except Exception as e:
                logger.warning(f"Error calculando {nombre_metrica}: {e}")
                evaluacion[nombre_metrica] = np.nan
        
        # Scores de validación cruzada
        cv_scores = cross_val_score(modelo, X, y, cv=cv, scoring='neg_mean_squared_error')
        evaluacion['cv_rmse_mean'] = np.sqrt(-cv_scores.mean())
        evaluacion['cv_rmse_std'] = np.sqrt(cv_scores.std())
        
        return evaluacion
    
    def comparar_modelos(self, X: pd.DataFrame, y: pd.Series, 
                        modelos: List[str], metodo: str = 'random_search',
                        **kwargs) -> Dict:
        """Compara múltiples modelos usando el método de optimización especificado"""
        
        logger.info(f"Comparando {len(modelos)} modelos usando {metodo}")
        
        resultados_comparacion = {}
        
        for modelo in modelos:
            try:
                if metodo == 'grid_search':
                    resultado = self.optimizar_grid_search(X, y, modelo, **kwargs)
                elif metodo == 'random_search':
                    resultado = self.optimizar_random_search(X, y, modelo, **kwargs)
                elif metodo == 'bayesian_search':
                    resultado = self.optimizar_bayesian_search(X, y, modelo, **kwargs)
                elif metodo == 'optuna':
                    resultado = self.optimizar_optuna(X, y, modelo, **kwargs)
                else:
                    raise ValueError(f"Método no soportado: {metodo}")
                
                resultados_comparacion[modelo] = resultado
                
            except Exception as e:
                logger.error(f"Error optimizando {modelo}: {e}")
                resultados_comparacion[modelo] = {'error': str(e)}
        
        # Encontrar mejor modelo
        mejor_modelo = None
        mejor_score = float('-inf')
        
        for modelo, resultado in resultados_comparacion.items():
            if 'error' not in resultado and resultado['mejor_score'] > mejor_score:
                mejor_score = resultado['mejor_score']
                mejor_modelo = modelo
        
        return {
            'resultados': resultados_comparacion,
            'mejor_modelo': mejor_modelo,
            'resumen': self._generar_resumen_comparacion(resultados_comparacion)
        }
    
    def _generar_resumen_comparacion(self, resultados: Dict) -> pd.DataFrame:
        """Genera un DataFrame resumen de la comparación"""
        
        datos_resumen = []
        
        for modelo, resultado in resultados.items():
            if 'error' in resultado:
                continue
            
            fila = {
                'Modelo': modelo,
                'Método': resultado['metodo'],
                'Mejor Score': resultado['mejor_score'],
                'RMSE': resultado['evaluacion'].get('rmse', np.nan),
                'MAE': resultado['evaluacion'].get('mae', np.nan),
                'R²': resultado['evaluacion'].get('r2', np.nan),
                'MAPE': resultado['evaluacion'].get('mape', np.nan),
                'Tiempo (s)': resultado['tiempo_entrenamiento'],
                'CV RMSE': resultado['evaluacion'].get('cv_rmse_mean', np.nan)
            }
            datos_resumen.append(fila)
        
        df_resumen = pd.DataFrame(datos_resumen)
        if len(df_resumen) > 0:
            df_resumen = df_resumen.sort_values('Mejor Score', ascending=False)
        
        return df_resumen
    
    def analizar_curvas_validacion(self, X: pd.DataFrame, y: pd.Series, 
                                  nombre_modelo: str, parametro: str, 
                                  valores_param: List) -> Dict:
        """Analiza curvas de validación para un parámetro específico"""
        
        modelo_base = self._obtener_modelo(nombre_modelo)
        
        if len(X) > 100:
            cv = TimeSeriesSplit(n_splits=5)
        else:
            cv = 5
        
        train_scores, validation_scores = validation_curve(
            modelo_base, X, y,
            param_name=parametro,
            param_range=valores_param,
            cv=cv,
            scoring='neg_mean_squared_error',
            n_jobs=-1
        )
        
        # Convertir a RMSE
        train_rmse = np.sqrt(-train_scores)
        val_rmse = np.sqrt(-validation_scores)
        
        resultados = {
            'parametro': parametro,
            'valores': valores_param,
            'train_rmse_mean': train_rmse.mean(axis=1),
            'train_rmse_std': train_rmse.std(axis=1),
            'val_rmse_mean': val_rmse.mean(axis=1),
            'val_rmse_std': val_rmse.std(axis=1),
            'mejor_valor': valores_param[np.argmin(val_rmse.mean(axis=1))]
        }
        
        return resultados
    
    def guardar_resultados(self, resultados: Dict, nombre_archivo: str = None) -> str:
        """Guarda los resultados de optimización"""
        
        if nombre_archivo is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nombre_archivo = f"optimizacion_{timestamp}.json"
        
        ruta_archivo = self.resultados_path / nombre_archivo
        
        # Preparar datos para serialización
        datos_serializables = self._preparar_para_serializacion(resultados)
        
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            json.dump(datos_serializables, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Resultados guardados en: {ruta_archivo}")
        return str(ruta_archivo)
    
    def _preparar_para_serializacion(self, obj):
        """Prepara objetos complejos para serialización JSON"""
        
        if isinstance(obj, dict):
            return {k: self._preparar_para_serializacion(v) for k, v in obj.items() 
                   if k not in ['modelo_entrenado', 'cv_results', 'estudio_optuna']}
        elif isinstance(obj, (list, tuple)):
            return [self._preparar_para_serializacion(item) for item in obj]
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict('records')
        elif hasattr(obj, '__dict__'):
            return str(obj)
        else:
            return obj
    
    def cargar_resultados(self, nombre_archivo: str) -> Dict:
        """Carga resultados de optimización guardados"""
        
        ruta_archivo = self.resultados_path / nombre_archivo
        
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            resultados = json.load(f)
        
        return resultados


def mostrar_optimizacion_hiperparametros():
    """Interfaz de Streamlit para optimización de hiperparámetros"""
    
    st.header("🎯 Optimización Avanzada de Hiperparámetros")
    st.markdown("### Tuning Automático para Modelos de Predicción de Llamadas")
    
    optimizador = OptimizadorHiperparametros()
    
    # Verificar disponibilidad de librerías opcionales
    with st.expander("ℹ️ Estado de Librerías Avanzadas", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_bayesian = "✅ Disponible" if BAYESIAN_AVAILABLE else "❌ No disponible"
            st.write(f"**Scikit-Optimize:** {status_bayesian}")
            if not BAYESIAN_AVAILABLE:
                st.code("pip install scikit-optimize")
        
        with col2:
            status_optuna = "✅ Disponible" if OPTUNA_AVAILABLE else "❌ No disponible"
            st.write(f"**Optuna:** {status_optuna}")
            if not OPTUNA_AVAILABLE:
                st.code("pip install optuna")
        
        with col3:
            status_prophet = "✅ Disponible" if PROPHET_AVAILABLE else "❌ No disponible"
            st.write(f"**Prophet:** {status_prophet}")
            if not PROPHET_AVAILABLE:
                st.code("pip install prophet")
    
    # Tabs para diferentes tipos de optimización
    tab_single, tab_compare, tab_curves, tab_results = st.tabs([
        "🎯 Modelo Individual", 
        "🏆 Comparar Modelos", 
        "📈 Curvas de Validación",
        "📊 Resultados Guardados"
    ])
    
    with tab_single:
        st.subheader("Optimización de Modelo Individual")
        
        # Selección de modelo
        col1, col2 = st.columns(2)
        
        with col1:
            modelos_disponibles = list(optimizador.espacios_busqueda.keys())
            modelo_seleccionado = st.selectbox("Modelo a optimizar", modelos_disponibles)
        
        with col2:
            metodos = ['Grid Search', 'Random Search']
            if BAYESIAN_AVAILABLE:
                metodos.append('Bayesian Search')
            if OPTUNA_AVAILABLE:
                metodos.append('Optuna')
            
            metodo_seleccionado = st.selectbox("Método de optimización", metodos)
        
        # Configuración de parámetros
        st.subheader("⚙️ Configuración de Optimización")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cv_folds = st.slider("Folds de validación cruzada", 3, 10, 5)
        
        with col2:
            if metodo_seleccionado in ['Random Search', 'Optuna']:
                n_iter = st.slider("Número de iteraciones", 10, 200, 50)
            else:
                n_iter = None
        
        with col3:
            usar_scaler = st.checkbox("Aplicar escalado de features", value=True)
            if usar_scaler:
                tipo_scaler = st.selectbox("Tipo de scaler", 
                                         ["StandardScaler", "MinMaxScaler", "RobustScaler"])
        
        # Mostrar espacio de búsqueda
        with st.expander(f"🔍 Espacio de Búsqueda - {modelo_seleccionado}"):
            if metodo_seleccionado == 'Grid Search':
                espacio = optimizador.espacios_busqueda[modelo_seleccionado]['grid']
            else:
                espacio = optimizador.espacios_busqueda[modelo_seleccionado]['random']
            
            for param, valores in espacio.items():
                st.write(f"**{param}:** {valores}")
        
        # Simulación con datos de ejemplo (en implementación real usar datos reales)
        if st.button("🚀 Iniciar Optimización", type="primary"):
            with st.spinner("Generando datos de ejemplo y ejecutando optimización..."):
                # Generar datos sintéticos para demostración
                np.random.seed(42)
                n_samples = 1000
                n_features = 10
                
                X = pd.DataFrame(
                    np.random.randn(n_samples, n_features),
                    columns=[f'feature_{i}' for i in range(n_features)]
                )
                y = pd.Series(
                    X.sum(axis=1) + np.random.randn(n_samples) * 0.1,
                    name='target'
                )
                
                # Aplicar escalado si está seleccionado
                if usar_scaler:
                    from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
                    scalers = {
                        'StandardScaler': StandardScaler(),
                        'MinMaxScaler': MinMaxScaler(),
                        'RobustScaler': RobustScaler()
                    }
                    scaler = scalers[tipo_scaler]
                    X_scaled = pd.DataFrame(
                        scaler.fit_transform(X),
                        columns=X.columns,
                        index=X.index
                    )
                    X = X_scaled
                
                try:
                    # Ejecutar optimización según el método seleccionado
                    if metodo_seleccionado == 'Grid Search':
                        resultados = optimizador.optimizar_grid_search(
                            X, y, modelo_seleccionado, cv_folds
                        )
                    elif metodo_seleccionado == 'Random Search':
                        resultados = optimizador.optimizar_random_search(
                            X, y, modelo_seleccionado, n_iter, cv_folds
                        )
                    elif metodo_seleccionado == 'Bayesian Search':
                        resultados = optimizador.optimizar_bayesian_search(
                            X, y, modelo_seleccionado, n_iter, cv_folds
                        )
                    elif metodo_seleccionado == 'Optuna':
                        resultados = optimizador.optimizar_optuna(
                            X, y, modelo_seleccionado, n_iter, cv_folds
                        )
                    
                    # Mostrar resultados
                    st.success("✅ Optimización completada exitosamente!")
                    
                    # Métricas principales
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Mejor Score", f"{resultados['mejor_score']:.4f}")
                    with col2:
                        st.metric("RMSE", f"{resultados['evaluacion']['rmse']:.4f}")
                    with col3:
                        st.metric("R²", f"{resultados['evaluacion']['r2']:.4f}")
                    with col4:
                        st.metric("Tiempo (s)", f"{resultados['tiempo_entrenamiento']:.2f}")
                    
                    # Mejores parámetros
                    st.subheader("🏆 Mejores Hiperparámetros")
                    for param, valor in resultados['mejores_parametros'].items():
                        st.write(f"**{param}:** {valor}")
                    
                    # Evaluación detallada
                    st.subheader("📊 Evaluación Detallada")
                    eval_df = pd.DataFrame([resultados['evaluacion']]).T
                    eval_df.columns = ['Valor']
                    st.dataframe(eval_df)
                    
                    # Guardar resultados
                    if st.button("💾 Guardar Resultados"):
                        archivo_guardado = optimizador.guardar_resultados(
                            resultados, 
                            f"{modelo_seleccionado}_{metodo_seleccionado.replace(' ', '_').lower()}.json"
                        )
                        st.success(f"Resultados guardados en: {archivo_guardado}")
                    
                except Exception as e:
                    st.error(f"Error durante la optimización: {str(e)}")
                    logger.error(f"Error en optimización: {e}")
    
    with tab_compare:
        st.subheader("Comparación de Múltiples Modelos")
        
        # Selección de modelos para comparar
        modelos_disponibles = list(optimizador.espacios_busqueda.keys())
        modelos_seleccionados = st.multiselect(
            "Selecciona modelos para comparar",
            modelos_disponibles,
            default=modelos_disponibles[:3]
        )
        
        if len(modelos_seleccionados) < 2:
            st.warning("Selecciona al menos 2 modelos para comparar")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                metodos_comp = ['random_search']
                if BAYESIAN_AVAILABLE:
                    metodos_comp.append('bayesian_search')
                if OPTUNA_AVAILABLE:
                    metodos_comp.append('optuna')
                
                metodo_comp = st.selectbox("Método de optimización", metodos_comp)
            
            with col2:
                n_iter_comp = st.slider("Iteraciones por modelo", 10, 100, 30)
            
            if st.button("🏁 Iniciar Comparación", type="primary"):
                with st.spinner(f"Comparando {len(modelos_seleccionados)} modelos..."):
                    # Generar datos sintéticos
                    np.random.seed(42)
                    n_samples = 500
                    n_features = 8
                    
                    X = pd.DataFrame(
                        np.random.randn(n_samples, n_features),
                        columns=[f'feature_{i}' for i in range(n_features)]
                    )
                    y = pd.Series(
                        X.sum(axis=1) + np.random.randn(n_samples) * 0.1,
                        name='target'
                    )
                    
                    try:
                        resultados_comp = optimizador.comparar_modelos(
                            X, y, modelos_seleccionados, metodo_comp,
                            n_iter=n_iter_comp, cv_folds=5
                        )
                        
                        st.success("✅ Comparación completada!")
                        
                        # Mostrar mejor modelo
                        st.subheader(f"🏆 Mejor Modelo: {resultados_comp['mejor_modelo']}")
                        
                        # Tabla resumen
                        st.subheader("📊 Resumen de Comparación")
                        df_resumen = resultados_comp['resumen']
                        st.dataframe(df_resumen, use_container_width=True)
                        
                        # Gráfico de comparación
                        if len(df_resumen) > 0:
                            st.subheader("📈 Comparación Visual")
                            
                            import plotly.express as px
                            import plotly.graph_objects as go
                            
                            # Gráfico de barras para múltiples métricas
                            fig = go.Figure()
                            
                            fig.add_trace(go.Bar(
                                name='RMSE',
                                x=df_resumen['Modelo'],
                                y=df_resumen['RMSE'],
                                yaxis='y'
                            ))
                            
                            fig.add_trace(go.Bar(
                                name='R²',
                                x=df_resumen['Modelo'],
                                y=df_resumen['R²'],
                                yaxis='y2'
                            ))
                            
                            fig.update_layout(
                                title='Comparación de Modelos: RMSE vs R²',
                                xaxis_title='Modelo',
                                yaxis=dict(title='RMSE', side='left'),
                                yaxis2=dict(title='R²', side='right', overlaying='y'),
                                barmode='group',
                                height=500
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Guardar comparación
                        if st.button("💾 Guardar Comparación"):
                            archivo_comp = optimizador.guardar_resultados(
                                resultados_comp,
                                f"comparacion_{metodo_comp}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                            )
                            st.success(f"Comparación guardada en: {archivo_comp}")
                    
                    except Exception as e:
                        st.error(f"Error durante la comparación: {str(e)}")
    
    with tab_curves:
        st.subheader("📈 Análisis de Curvas de Validación")
        
        st.info("Analiza cómo afecta un hiperparámetro específico al rendimiento del modelo")
        
        col1, col2 = st.columns(2)
        
        with col1:
            modelo_curvas = st.selectbox("Modelo", list(optimizador.espacios_busqueda.keys()))
        
        with col2:
            # Parámetros disponibles según el modelo
            params_disponibles = list(optimizador.espacios_busqueda[modelo_curvas]['grid'].keys())
            parametro_analizar = st.selectbox("Parámetro a analizar", params_disponibles)
        
        # Definir rango de valores para el parámetro
        st.subheader("📊 Configuración del Análisis")
        
        if parametro_analizar in ['n_estimators', 'max_depth', 'min_samples_split']:
            valores_min = st.number_input("Valor mínimo", value=10, min_value=1)
            valores_max = st.number_input("Valor máximo", value=200, min_value=int(valores_min))
            n_puntos = st.slider("Número de puntos", 5, 20, 10)
            valores_param = np.linspace(int(valores_min), int(valores_max), n_puntos, dtype=int)
        else:
            st.info("Configuración automática para este parámetro")
            valores_param = optimizador.espacios_busqueda[modelo_curvas]['grid'][parametro_analizar]
        
        if st.button("📊 Generar Curvas de Validación"):
            with st.spinner("Analizando curvas de validación..."):
                # Datos sintéticos
                np.random.seed(42)
                X = pd.DataFrame(np.random.randn(300, 5), columns=[f'feature_{i}' for i in range(5)])
                y = pd.Series(X.sum(axis=1) + np.random.randn(300) * 0.1)
                
                try:
                    resultados_curvas = optimizador.analizar_curvas_validacion(
                        X, y, modelo_curvas, parametro_analizar, valores_param
                    )
                    
                    st.success("✅ Análisis completado!")
                    
                    # Mostrar mejor valor
                    st.metric("🎯 Mejor Valor", resultados_curvas['mejor_valor'])
                    
                    # Gráfico de curvas
                    import plotly.graph_objects as go
                    
                    fig = go.Figure()
                    
                    # Curva de entrenamiento
                    fig.add_trace(go.Scatter(
                        x=resultados_curvas['valores'],
                        y=resultados_curvas['train_rmse_mean'],
                        mode='lines+markers',
                        name='Training RMSE',
                        line=dict(color='blue'),
                        error_y=dict(array=resultados_curvas['train_rmse_std'])
                    ))
                    
                    # Curva de validación
                    fig.add_trace(go.Scatter(
                        x=resultados_curvas['valores'],
                        y=resultados_curvas['val_rmse_mean'],
                        mode='lines+markers',
                        name='Validation RMSE',
                        line=dict(color='red'),
                        error_y=dict(array=resultados_curvas['val_rmse_std'])
                    ))
                    
                    # Línea del mejor valor
                    fig.add_vline(
                        x=resultados_curvas['mejor_valor'],
                        line_dash="dash",
                        line_color="green",
                        annotation_text="Mejor valor"
                    )
                    
                    fig.update_layout(
                        title=f'Curvas de Validación - {parametro_analizar}',
                        xaxis_title=parametro_analizar,
                        yaxis_title='RMSE',
                        height=500
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Tabla de resultados
                    st.subheader("📋 Resultados Detallados")
                    curvas_df = pd.DataFrame({
                        parametro_analizar: resultados_curvas['valores'],
                        'Train RMSE': resultados_curvas['train_rmse_mean'],
                        'Train Std': resultados_curvas['train_rmse_std'],
                        'Val RMSE': resultados_curvas['val_rmse_mean'],
                        'Val Std': resultados_curvas['val_rmse_std']
                    })
                    st.dataframe(curvas_df)
                
                except Exception as e:
                    st.error(f"Error en análisis de curvas: {str(e)}")
    
    with tab_results:
        st.subheader("📊 Gestión de Resultados Guardados")
        
        # Listar archivos de resultados
        archivos_resultados = list(optimizador.resultados_path.glob("*.json"))
        
        if not archivos_resultados:
            st.info("No hay resultados guardados aún")
        else:
            # Seleccionar archivo
            nombres_archivos = [f.name for f in archivos_resultados]
            archivo_seleccionado = st.selectbox("Seleccionar archivo de resultados", nombres_archivos)
            
            if archivo_seleccionado:
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("📖 Cargar y Mostrar"):
                        try:
                            resultados_cargados = optimizador.cargar_resultados(archivo_seleccionado)
                            
                            st.success("✅ Resultados cargados exitosamente")
                            
                            # Mostrar información general
                            if isinstance(resultados_cargados, dict) and 'metodo' in resultados_cargados:
                                # Resultado individual
                                st.subheader("📊 Información General")
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.metric("Modelo", resultados_cargados.get('modelo', 'N/A'))
                                with col2:
                                    st.metric("Método", resultados_cargados.get('metodo', 'N/A'))
                                with col3:
                                    st.metric("Mejor Score", f"{resultados_cargados.get('mejor_score', 0):.4f}")
                                
                                # Mejores parámetros
                                if 'mejores_parametros' in resultados_cargados:
                                    st.subheader("🏆 Mejores Parámetros")
                                    params_df = pd.DataFrame(
                                        list(resultados_cargados['mejores_parametros'].items()),
                                        columns=['Parámetro', 'Valor']
                                    )
                                    st.dataframe(params_df)
                                
                                # Evaluación
                                if 'evaluacion' in resultados_cargados:
                                    st.subheader("📈 Métricas de Evaluación")
                                    eval_df = pd.DataFrame(
                                        list(resultados_cargados['evaluacion'].items()),
                                        columns=['Métrica', 'Valor']
                                    )
                                    st.dataframe(eval_df)
                            
                            elif isinstance(resultados_cargados, dict) and 'resumen' in resultados_cargados:
                                # Comparación de modelos
                                st.subheader("🏆 Resumen de Comparación")
                                if isinstance(resultados_cargados['resumen'], list):
                                    df_resumen = pd.DataFrame(resultados_cargados['resumen'])
                                    st.dataframe(df_resumen)
                                
                                st.subheader(f"🥇 Mejor Modelo: {resultados_cargados.get('mejor_modelo', 'N/A')}")
                            
                            # Raw data
                            with st.expander("🔍 Datos Raw (JSON)"):
                                st.json(resultados_cargados)
                        
                        except Exception as e:
                            st.error(f"Error cargando resultados: {str(e)}")
                
                with col2:
                    if st.button("🗑️ Eliminar Archivo"):
                        try:
                            archivo_path = optimizador.resultados_path / archivo_seleccionado
                            archivo_path.unlink()
                            st.success("✅ Archivo eliminado")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error eliminando archivo: {str(e)}")


if __name__ == "__main__":
    # Para testing directo
    optimizador = OptimizadorHiperparametros()
    print("Optimizador de hiperparámetros inicializado correctamente")