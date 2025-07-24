#!/usr/bin/env python3
"""
CEAPSI - Sistema Multi-Modelo Especializado para Predicción de Llamadas
Combina ARIMA, Prophet, y modelos de Machine Learning
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import pickle
import warnings
warnings.filterwarnings('ignore')

# Imports para modelos
from prophet import Prophet
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler

class SistemaMultiModeloCEAPSI:
    """Sistema híbrido de múltiples modelos para predicción de llamadas"""
    
    def __init__(self, config_path=None):
        self.modelos = {}
        self.metadatos = {}
        self.predicciones_historicas = {}
        self.pesos_ensemble = {}
        self.config = self._cargar_config(config_path)
        
    def _cargar_config(self, config_path):
        """Carga configuración del sistema"""
        config_default = {
            'horizontes_prediccion': [1, 3, 7, 14, 28],  # días
            'ventana_validacion': 30,  # días para validación
            'metrica_principal': 'mae',
            'umbral_precision': 15.0,  # MAE máximo aceptable
            'modelos_activos': ['arima', 'prophet', 'random_forest', 'gradient_boosting'],
            'pesos_iniciales': {'arima': 0.3, 'prophet': 0.3, 'random_forest': 0.2, 'gradient_boosting': 0.2}
        }
        
        if config_path:
            try:
                with open(config_path, 'r') as f:
                    config_usuario = json.load(f)
                config_default.update(config_usuario)
            except Exception as e:
                print(f"⚠️ Error cargando config: {e}, usando configuración por defecto")
        
        return config_default
    
    def cargar_datos_segmentados(self, tipo_llamada='ENTRANTE'):
        """Carga datos segmentados por tipo de llamada con filtrado de feriados según regulación chilena"""
        
        # Usar directorio actual del script
        from pathlib import Path
        base_path = Path(__file__).parent.absolute()
        archivo_datos = base_path / f"datos_prophet_{tipo_llamada.lower()}.csv"
        
        try:
            df = pd.read_csv(archivo_datos)
            df['ds'] = pd.to_datetime(df['ds'])
            df = df.sort_values('ds').reset_index(drop=True)
            
            print(f"✅ Datos cargados: {len(df)} días de {tipo_llamada.lower()}")
            print(f"📅 Período: {df['ds'].min().date()} a {df['ds'].max().date()}")
            print(f"📊 Promedio diario antes filtrado: {df['y'].mean():.1f} llamadas")
            
            # Aplicar filtrado de feriados según normativa chilena
            try:
                from feriados_chilenos import GestorFeriadosChilenos
                gestor_feriados = GestorFeriadosChilenos()
                
                # Filtrar datos para entrenamiento según tipo de llamada
                df_filtrado = gestor_feriados.filtrar_datos_para_entrenamiento(df, tipo_llamada)
                
                if len(df_filtrado) < len(df):
                    registros_filtrados = len(df) - len(df_filtrado)
                    if tipo_llamada.lower() in ['saliente', 'outbound', 'out']:
                        print(f"🇨🇱 Feriados chilenos filtrados: {registros_filtrados} días excluidos del entrenamiento (llamadas salientes)")
                    else:
                        print(f"🇨🇱 Llamadas entrantes: {len(df_filtrado)} registros mantenidos (incluyendo feriados para pronóstico de demanda)")
                
                print(f"📊 Promedio diario después filtrado: {df_filtrado['y'].mean():.1f} llamadas")
                return df_filtrado
                
            except ImportError:
                print("⚠️ Módulo de feriados chilenos no disponible, usando datos sin filtrar")
                return df
            except Exception as e:
                print(f"⚠️ Error aplicando filtros de feriados: {e}, usando datos sin filtrar")
                return df
            
        except FileNotFoundError:
            print(f"❌ No se encontró archivo: {archivo_datos}")
            print("💡 Ejecutar segmentación de datos primero")
            return None
        except Exception as e:
            print(f"❌ Error cargando datos: {e}")
            return None
    
    def preparar_features_avanzadas(self, df):
        """Genera features avanzadas para modelos ML"""
        
        df_features = df.copy()
        
        # Features temporales básicas
        df_features['dia_semana'] = df_features['ds'].dt.dayofweek + 1
        df_features['dia_mes'] = df_features['ds'].dt.day
        df_features['semana_ano'] = df_features['ds'].dt.isocalendar().week
        df_features['mes'] = df_features['ds'].dt.month
        df_features['trimestre'] = df_features['ds'].dt.quarter
        
        # Features cíclicas (mejor para ML)
        df_features['dia_semana_sin'] = np.sin(2 * np.pi * df_features['dia_semana'] / 7)
        df_features['dia_semana_cos'] = np.cos(2 * np.pi * df_features['dia_semana'] / 7)
        df_features['mes_sin'] = np.sin(2 * np.pi * df_features['mes'] / 12)
        df_features['mes_cos'] = np.cos(2 * np.pi * df_features['mes'] / 12)
        
        # Features de lag (valores pasados)
        for lag in [1, 2, 3, 7, 14]:
            df_features[f'lag_{lag}'] = df_features['y'].shift(lag)
        
        # Features de ventana móvil
        for ventana in [3, 7, 14]:
            df_features[f'media_movil_{ventana}'] = df_features['y'].rolling(ventana).mean()
            df_features[f'std_movil_{ventana}'] = df_features['y'].rolling(ventana).std()
        
        # Features de tendencia
        df_features['tendencia_7d'] = df_features['y'].rolling(7).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == 7 else np.nan
        )
        
        # Features de estacionalidad semanal
        df_features['promedio_dia_semana'] = df_features.groupby('dia_semana')['y'].transform('mean')
        df_features['desviacion_vs_promedio_dia'] = df_features['y'] - df_features['promedio_dia_semana']
        
        # Features de outliers/anomalías
        rolling_mean = df_features['y'].rolling(14, center=True).mean()
        rolling_std = df_features['y'].rolling(14, center=True).std()
        df_features['z_score'] = (df_features['y'] - rolling_mean) / rolling_std
        df_features['es_outlier'] = (np.abs(df_features['z_score']) > 2).astype(int)
        
        # Limpiar NaN generados por lag y rolling
        df_features = df_features.dropna().reset_index(drop=True)
        
        print(f"🔧 Features generadas: {len(df_features.columns)} columnas")
        print(f"📊 Datos después de limpieza: {len(df_features)} registros")
        
        return df_features
    
    def entrenar_modelo_arima(self, df, horizonte=7):
        """Entrena modelo ARIMA optimizado"""
        
        print(f"🤖 Entrenando ARIMA para horizonte {horizonte} días...")
        
        # Preparar datos
        y_train = df['y'].values
        
        # Búsqueda automática de mejores parámetros ARIMA
        mejor_aic = float('inf')
        mejor_modelo = None
        mejor_params = None
        
        # Grid search limitado para eficiencia
        p_range = range(0, 3)
        d_range = range(0, 2)  
        q_range = range(0, 3)
        seasonal_range = [(0,0,0,0), (1,1,1,7)]  # Sin estacionalidad y estacionalidad semanal
        
        for p in p_range:
            for d in d_range:
                for q in q_range:
                    for seasonal in seasonal_range:
                        try:
                            modelo = SARIMAX(y_train, 
                                           order=(p, d, q), 
                                           seasonal_order=seasonal,
                                           enforce_stationarity=False,
                                           enforce_invertibility=False)
                            
                            modelo_fit = modelo.fit(disp=False, maxiter=100)
                            
                            if modelo_fit.aic < mejor_aic:
                                mejor_aic = modelo_fit.aic
                                mejor_modelo = modelo_fit
                                mejor_params = {'order': (p, d, q), 'seasonal_order': seasonal}
                                
                        except Exception:
                            continue
        
        if mejor_modelo is None:
            # Fallback a modelo simple
            print("⚠️ Usando ARIMA(1,1,1) como fallback")
            modelo_simple = SARIMAX(y_train, order=(1, 1, 1))
            mejor_modelo = modelo_simple.fit(disp=False)
            mejor_params = {'order': (1, 1, 1), 'seasonal_order': (0, 0, 0, 0)}
        
        # Guardar modelo
        self.modelos['arima'] = mejor_modelo
        self.metadatos['arima'] = {
            'parametros': mejor_params,
            'aic': float(mejor_modelo.aic),
            'horizonte_entrenamiento': horizonte,
            'fecha_entrenamiento': datetime.now().isoformat()
        }
        
        print(f"✅ ARIMA entrenado: {mejor_params['order']} AIC={mejor_modelo.aic:.2f}")
        return mejor_modelo
    
    def entrenar_modelo_prophet(self, df, horizonte=7):
        """Entrena modelo Prophet optimizado para llamadas"""
        
        print(f"🔮 Entrenando Prophet para horizonte {horizonte} días...")
        
        # Configuración específica para llamadas de call center
        modelo_prophet = Prophet(
            yearly_seasonality=False,  # No hay suficientes datos anuales
            weekly_seasonality=True,   # Fuerte patrón semanal
            daily_seasonality=False,   # Datos diarios agregados
            changepoint_prior_scale=0.05,  # Menos sensible a cambios
            seasonality_prior_scale=10.0,  # Estacionalidad moderada
            holidays_prior_scale=10.0,
            seasonality_mode='additive',
            interval_width=0.80,
            mcmc_samples=0  # Sin MCMC para mayor velocidad
        )
        
        # Agregar regresores disponibles
        columnas_regresores = ['dia_semana', 'es_inicio_mes', 'semana_mes']
        for regresor in columnas_regresores:
            if regresor in df.columns:
                modelo_prophet.add_regressor(regresor, prior_scale=10.0)
        
        # Datos para Prophet
        df_prophet = df[['ds', 'y'] + [col for col in columnas_regresores if col in df.columns]].copy()
        
        # Entrenar
        modelo_prophet.fit(df_prophet)
        
        # Guardar modelo
        self.modelos['prophet'] = modelo_prophet
        self.metadatos['prophet'] = {
            'regresores_utilizados': columnas_regresores,
            'horizonte_entrenamiento': horizonte,
            'fecha_entrenamiento': datetime.now().isoformat(),
            'parametros': {
                'changepoint_prior_scale': 0.05,
                'seasonality_prior_scale': 10.0,
                'seasonality_mode': 'additive'
            }
        }
        
        print(f"✅ Prophet entrenado con {len(columnas_regresores)} regresores")
        return modelo_prophet
    
    def entrenar_modelos_ml(self, df, horizonte=7):
        """Entrena modelos de Machine Learning"""
        
        print(f"🧠 Entrenando modelos ML para horizonte {horizonte} días...")
        
        # Preparar features
        df_features = self.preparar_features_avanzadas(df)
        
        # Seleccionar features para ML (excluir ds, y, y variables objetivo futuras)
        feature_columns = [col for col in df_features.columns 
                          if col not in ['ds', 'y', 'fecha_str'] and not col.startswith('target_')]
        
        X = df_features[feature_columns].copy()
        y = df_features['y'].copy()
        
        # Dividir datos manteniendo orden temporal
        split_point = int(len(df_features) * 0.8)
        X_train, X_test = X.iloc[:split_point], X.iloc[split_point:]
        y_train, y_test = y.iloc[:split_point], y.iloc[split_point:]
        
        # Escalar features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Configurar modelos
        modelos_ml = {
            'random_forest': RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            ),
            'gradient_boosting': GradientBoostingRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                random_state=42
            ),
            'ridge': Ridge(alpha=1.0)
        }
        
        # Entrenar cada modelo
        for nombre, modelo in modelos_ml.items():
            try:
                if nombre == 'ridge':
                    modelo.fit(X_train_scaled, y_train)
                    y_pred_test = modelo.predict(X_test_scaled)
                else:
                    modelo.fit(X_train, y_train)
                    y_pred_test = modelo.predict(X_test)
                
                # Métricas de validación
                mae_test = mean_absolute_error(y_test, y_pred_test)
                rmse_test = np.sqrt(mean_squared_error(y_test, y_pred_test))
                
                # Guardar modelo y metadatos
                self.modelos[nombre] = modelo
                self.metadatos[nombre] = {
                    'features_utilizadas': feature_columns,
                    'mae_validacion': float(mae_test),
                    'rmse_validacion': float(rmse_test),
                    'horizonte_entrenamiento': horizonte,
                    'fecha_entrenamiento': datetime.now().isoformat(),
                    'scaler': scaler if nombre == 'ridge' else None
                }
                
                print(f"✅ {nombre}: MAE={mae_test:.2f}, RMSE={rmse_test:.2f}")
                
            except Exception as e:
                print(f"❌ Error entrenando {nombre}: {e}")
        
        return X_train, X_test, y_train, y_test
    
    def validacion_cruzada_temporal(self, df, horizonte=7):
        """Validación cruzada respetando orden temporal"""
        
        print(f"🔍 Ejecutando validación cruzada temporal...")
        
        resultados_cv = {}
        
        # Configurar validación temporal
        n_splits = 5
        gap = horizonte  # Gap entre entrenamiento y test
        
        # Splits temporales manuales
        total_size = len(df)
        test_size = total_size // (n_splits + 1)
        
        for fold in range(n_splits):
            print(f"   Fold {fold + 1}/{n_splits}")
            
            # Definir índices de entrenamiento y test
            test_end = total_size - fold * test_size
            test_start = test_end - test_size
            train_end = test_start - gap
            
            if train_end < test_size:  # Datos insuficientes
                continue
            
            # Dividir datos
            df_train = df.iloc[:train_end].copy()
            df_test = df.iloc[test_start:test_end].copy()
            
            # Entrenar modelos temporalmente en este fold
            if 'arima' in self.config['modelos_activos']:
                modelo_arima = self.entrenar_modelo_arima(df_train, horizonte)
                pred_arima = modelo_arima.forecast(steps=len(df_test))
                
                if 'arima' not in resultados_cv:
                    resultados_cv['arima'] = []
                resultados_cv['arima'].append({
                    'y_true': df_test['y'].values,
                    'y_pred': pred_arima
                })
            
            # Prophet requiere datos futuros con regresores
            if 'prophet' in self.config['modelos_activos']:
                modelo_prophet = self.entrenar_modelo_prophet(df_train, horizonte)
                
                # Crear future dataframe
                future = modelo_prophet.make_future_dataframe(periods=len(df_test))
                
                # Agregar regresores si existen
                for col in ['dia_semana', 'es_inicio_mes', 'semana_mes']:
                    if col in df.columns:
                        # Extender regresores para fechas futuras
                        future[col] = pd.concat([
                            df_train[col],
                            df_test[col]
                        ]).values[:len(future)]
                
                forecast = modelo_prophet.predict(future)
                pred_prophet = forecast['yhat'].tail(len(df_test)).values
                
                if 'prophet' not in resultados_cv:
                    resultados_cv['prophet'] = []
                resultados_cv['prophet'].append({
                    'y_true': df_test['y'].values,
                    'y_pred': pred_prophet
                })
        
        # Calcular métricas promedio de CV
        metricas_cv = {}
        for modelo, resultados in resultados_cv.items():
            y_true_all = np.concatenate([r['y_true'] for r in resultados])
            y_pred_all = np.concatenate([r['y_pred'] for r in resultados])
            
            metricas_cv[modelo] = {
                'mae_cv': float(mean_absolute_error(y_true_all, y_pred_all)),
                'rmse_cv': float(np.sqrt(mean_squared_error(y_true_all, y_pred_all))),
                'mape_cv': float(mean_absolute_percentage_error(y_true_all, y_pred_all)) * 100,
                'n_predictions': len(y_true_all)
            }
        
        print(f"📊 RESULTADOS VALIDACIÓN CRUZADA:")
        for modelo, metricas in metricas_cv.items():
            print(f"   {modelo}: MAE={metricas['mae_cv']:.2f}, RMSE={metricas['rmse_cv']:.2f}, MAPE={metricas['mape_cv']:.1f}%")
        
        return metricas_cv
    
    def calcular_pesos_ensemble(self, metricas_cv):
        """Calcula pesos óptimos para ensemble basado en performance"""
        
        print("⚖️ Calculando pesos óptimos para ensemble...")
        
        # Usar MAE como métrica principal (menor es mejor)
        mae_scores = {modelo: metricas['mae_cv'] for modelo, metricas in metricas_cv.items()}
        
        # Invertir MAE para que mayor sea mejor
        mae_invertido = {modelo: 1 / mae for modelo, mae in mae_scores.items()}
        
        # Normalizar para que sumen 1
        suma_total = sum(mae_invertido.values())
        pesos = {modelo: peso / suma_total for modelo, peso in mae_invertido.items()}
        
        # Aplicar suavizado para evitar pesos extremos
        min_peso = 0.1
        max_peso = 0.5
        
        pesos_suavizados = {}
        for modelo, peso in pesos.items():
            peso_ajustado = max(min_peso, min(max_peso, peso))
            pesos_suavizados[modelo] = peso_ajustado
        
        # Renormalizar después del suavizado
        suma_suavizada = sum(pesos_suavizados.values())
        pesos_finales = {modelo: peso / suma_suavizada for modelo, peso in pesos_suavizados.items()}
        
        self.pesos_ensemble = pesos_finales
        
        print("🏆 PESOS FINALES DEL ENSEMBLE:")
        for modelo, peso in pesos_finales.items():
            print(f"   {modelo}: {peso:.3f} (MAE: {mae_scores.get(modelo, 0):.2f})")
        
        return pesos_finales
    
    def generar_predicciones_ensemble(self, df, dias_futuro=28):
        """Genera predicciones usando ensemble de todos los modelos"""
        
        print(f"🔮 Generando predicciones ensemble para {dias_futuro} días...")
        
        predicciones_individuales = {}
        
        # Generar fechas futuras (solo días laborales)
        ultima_fecha = df['ds'].max()
        fechas_futuras = []
        fecha_actual = ultima_fecha + timedelta(days=1)
        
        while len(fechas_futuras) < dias_futuro:
            if fecha_actual.weekday() < 5:  # Lunes a viernes
                fechas_futuras.append(fecha_actual)
            fecha_actual += timedelta(days=1)
        
        # ARIMA
        if 'arima' in self.modelos and 'arima' in self.pesos_ensemble:
            try:
                pred_arima = self.modelos['arima'].forecast(steps=len(fechas_futuras))
                predicciones_individuales['arima'] = pred_arima
                print(f"✅ ARIMA: {len(pred_arima)} predicciones")
            except Exception as e:
                print(f"❌ Error ARIMA: {e}")
        
        # Prophet
        if 'prophet' in self.modelos and 'prophet' in self.pesos_ensemble:
            try:
                modelo_prophet = self.modelos['prophet']
                
                # Crear future dataframe
                future = modelo_prophet.make_future_dataframe(periods=len(fechas_futuras))
                
                # Agregar regresores estimados para fechas futuras
                for col in ['dia_semana', 'es_inicio_mes', 'semana_mes']:
                    if col in df.columns:
                        # Extender regresores basado en patrones históricos
                        if col == 'dia_semana':
                            future[col] = future['ds'].dt.dayofweek + 1
                        elif col == 'es_inicio_mes':
                            future[col] = (future['ds'].dt.day <= 5).astype(int)
                        elif col == 'semana_mes':
                            future[col] = ((future['ds'].dt.day - 1) // 7) + 1
                
                forecast = modelo_prophet.predict(future)
                pred_prophet = forecast['yhat'].tail(len(fechas_futuras)).values
                predicciones_individuales['prophet'] = pred_prophet
                print(f"✅ Prophet: {len(pred_prophet)} predicciones")
            except Exception as e:
                print(f"❌ Error Prophet: {e}")
        
        # Modelos ML (requieren features futuras)
        if any(modelo in self.modelos for modelo in ['random_forest', 'gradient_boosting', 'ridge']):
            try:
                # Crear dataframe futuro con features
                df_futuro = pd.DataFrame({'ds': fechas_futuras})
                
                # Generar features básicas para fechas futuras
                df_futuro['dia_semana'] = df_futuro['ds'].dt.dayofweek + 1
                df_futuro['dia_mes'] = df_futuro['ds'].dt.day
                df_futuro['semana_ano'] = df_futuro['ds'].dt.isocalendar().week
                df_futuro['mes'] = df_futuro['ds'].dt.month
                df_futuro['trimestre'] = df_futuro['ds'].dt.quarter
                
                # Features cíclicas
                df_futuro['dia_semana_sin'] = np.sin(2 * np.pi * df_futuro['dia_semana'] / 7)
                df_futuro['dia_semana_cos'] = np.cos(2 * np.pi * df_futuro['dia_semana'] / 7)
                df_futuro['mes_sin'] = np.sin(2 * np.pi * df_futuro['mes'] / 12)
                df_futuro['mes_cos'] = np.cos(2 * np.pi * df_futuro['mes'] / 12)
                
                # Estimar features de lag usando últimos valores conocidos
                ultimos_valores = df['y'].tail(14).values
                for i, fecha in enumerate(fechas_futuras):
                    for lag in [1, 2, 3, 7, 14]:
                        if i >= lag:
                            # Usar predicción previa o valor conocido
                            df_futuro.loc[i, f'lag_{lag}'] = ultimos_valores[-(lag-i)] if (lag-i) <= len(ultimos_valores) else ultimos_valores[-1]
                        else:
                            df_futuro.loc[i, f'lag_{lag}'] = ultimos_valores[-(lag)] if lag <= len(ultimos_valores) else ultimos_valores[-1]
                
                # Features de ventana móvil (estimadas)
                for ventana in [3, 7, 14]:
                    df_futuro[f'media_movil_{ventana}'] = df['y'].tail(ventana).mean()
                    df_futuro[f'std_movil_{ventana}'] = df['y'].tail(ventana).std()
                
                # Otras features (valores por defecto)
                df_futuro['tendencia_7d'] = 0
                df_futuro['promedio_dia_semana'] = df.groupby(df['ds'].dt.dayofweek + 1)['y'].mean().reindex(df_futuro['dia_semana']).values
                df_futuro['desviacion_vs_promedio_dia'] = 0
                df_futuro['z_score'] = 0
                df_futuro['es_outlier'] = 0
                
                # Predecir con cada modelo ML
                feature_columns = self.metadatos.get('random_forest', {}).get('features_utilizadas', [])
                
                for modelo_name in ['random_forest', 'gradient_boosting', 'ridge']:
                    if modelo_name in self.modelos and modelo_name in self.pesos_ensemble:
                        try:
                            modelo = self.modelos[modelo_name]
                            
                            # Seleccionar y preparar features
                            X_futuro = df_futuro[feature_columns].fillna(0)
                            
                            if modelo_name == 'ridge' and 'scaler' in self.metadatos[modelo_name]:
                                scaler = self.metadatos[modelo_name]['scaler']
                                X_futuro_scaled = scaler.transform(X_futuro)
                                pred_ml = modelo.predict(X_futuro_scaled)
                            else:
                                pred_ml = modelo.predict(X_futuro)
                            
                            predicciones_individuales[modelo_name] = pred_ml
                            print(f"✅ {modelo_name}: {len(pred_ml)} predicciones")
                            
                        except Exception as e:
                            print(f"❌ Error {modelo_name}: {e}")
            
            except Exception as e:
                print(f"❌ Error generando features ML: {e}")
        
        # Combinar predicciones usando pesos del ensemble
        if not predicciones_individuales:
            print("❌ No se pudieron generar predicciones")
            return None
        
        # Calcular predicción ensemble
        prediccion_ensemble = np.zeros(len(fechas_futuras))
        suma_pesos = 0
        
        for modelo, predicciones in predicciones_individuales.items():
            if modelo in self.pesos_ensemble:
                peso = self.pesos_ensemble[modelo]
                prediccion_ensemble += peso * np.array(predicciones)
                suma_pesos += peso
        
        # Normalizar si los pesos no suman exactamente 1
        if suma_pesos > 0:
            prediccion_ensemble /= suma_pesos
        
        # Crear DataFrame de resultados
        df_predicciones = pd.DataFrame({
            'ds': fechas_futuras,
            'yhat_ensemble': prediccion_ensemble
        })
        
        # Agregar predicciones individuales
        for modelo, predicciones in predicciones_individuales.items():
            df_predicciones[f'yhat_{modelo}'] = predicciones
        
        # Calcular intervalos de confianza basados en dispersión de modelos
        predicciones_matriz = np.array([pred for pred in predicciones_individuales.values()]).T
        df_predicciones['yhat_std'] = np.std(predicciones_matriz, axis=1)
        df_predicciones['yhat_lower'] = df_predicciones['yhat_ensemble'] - 1.96 * df_predicciones['yhat_std']
        df_predicciones['yhat_upper'] = df_predicciones['yhat_ensemble'] + 1.96 * df_predicciones['yhat_std']
        
        # Asegurar valores no negativos
        df_predicciones['yhat_ensemble'] = np.maximum(0, df_predicciones['yhat_ensemble'])
        df_predicciones['yhat_lower'] = np.maximum(0, df_predicciones['yhat_lower'])
        
        print(f"🎯 PREDICCIONES ENSEMBLE GENERADAS:")
        print(f"   📅 Período: {df_predicciones['ds'].min().date()} a {df_predicciones['ds'].max().date()}")
        print(f"   📊 Promedio: {df_predicciones['yhat_ensemble'].mean():.1f} llamadas/día")
        print(f"   📈 Rango: {df_predicciones['yhat_ensemble'].min():.1f} - {df_predicciones['yhat_ensemble'].max():.1f}")
        
        # Validar que las fechas sean futuras respecto a los datos históricos
        fecha_limite_historica = df['ds'].max()
        fecha_primera_prediccion = df_predicciones['ds'].min()
        
        if fecha_primera_prediccion <= fecha_limite_historica:
            print(f"⚠️ ADVERTENCIA: Las predicciones se solapan con datos históricos")
            print(f"   Último histórico: {fecha_limite_historica.date()}")
            print(f"   Primera predicción: {fecha_primera_prediccion.date()}")
        else:
            print(f"✅ Separación temporal correcta:")
            print(f"   Último histórico: {fecha_limite_historica.date()}")
            print(f"   Primera predicción: {fecha_primera_prediccion.date()}")
        
        return df_predicciones
    
    def detectar_alertas_avanzadas(self, df_predicciones, df_historico):
        """Sistema avanzado de detección de alertas"""
        
        print("🚨 Detectando alertas avanzadas...")
        
        alertas = []
        
        # Calcular estadísticas históricas
        media_historica = df_historico['y'].mean()
        std_historica = df_historico['y'].std()
        percentil_90 = df_historico['y'].quantile(0.9)
        percentil_10 = df_historico['y'].quantile(0.1)
        
        # Umbrales dinámicos basados en datos históricos
        umbral_critico = media_historica + 2.5 * std_historica
        umbral_alto = media_historica + 1.5 * std_historica
        umbral_bajo = media_historica - 1.5 * std_historica
        
        for idx, row in df_predicciones.iterrows():
            fecha = row['ds'].date()
            prediccion = row['yhat_ensemble']
            incertidumbre = row['yhat_std']
            limite_superior = row['yhat_upper']
            
            # Alerta por demanda extrema
            if prediccion > umbral_critico:
                alertas.append({
                    'tipo': 'DEMANDA_EXTREMA',
                    'severidad': 'CRITICA',
                    'fecha': fecha.isoformat(),
                    'valor_predicho': round(prediccion, 1),
                    'umbral': round(umbral_critico, 1),
                    'mensaje': f'Demanda extrema predicha: {prediccion:.1f} llamadas (>+2.5σ histórico)',
                    'accion': 'Activar protocolo de emergencia, personal adicional urgente',
                    'confianza': min(0.95, 1 - (incertidumbre / prediccion)) if prediccion > 0 else 0.5
                })
            
            elif prediccion > umbral_alto:
                alertas.append({
                    'tipo': 'DEMANDA_ALTA',
                    'severidad': 'ALTA',
                    'fecha': fecha.isoformat(),
                    'valor_predicho': round(prediccion, 1),
                    'umbral': round(umbral_alto, 1),
                    'mensaje': f'Alta demanda predicha: {prediccion:.1f} llamadas (>+1.5σ histórico)',
                    'accion': 'Programar personal adicional, revisar capacidad',
                    'confianza': min(0.9, 1 - (incertidumbre / prediccion)) if prediccion > 0 else 0.5
                })
            
            # Alerta por demanda baja (posible sobredotación)
            elif prediccion < umbral_bajo:
                alertas.append({
                    'tipo': 'DEMANDA_BAJA',
                    'severidad': 'MEDIA',
                    'fecha': fecha.isoformat(),
                    'valor_predicho': round(prediccion, 1),
                    'umbral': round(umbral_bajo, 1),
                    'mensaje': f'Baja demanda predicha: {prediccion:.1f} llamadas (<-1.5σ histórico)',
                    'accion': 'Considerar reducir turnos o reasignar personal',
                    'confianza': min(0.85, 1 - (incertidumbre / abs(prediccion))) if prediccion != 0 else 0.5
                })
            
            # Alerta por alta incertidumbre
            if incertidumbre > prediccion * 0.3:  # Incertidumbre > 30% de la predicción
                alertas.append({
                    'tipo': 'ALTA_INCERTIDUMBRE',
                    'severidad': 'MEDIA',
                    'fecha': fecha.isoformat(),
                    'valor_predicho': round(prediccion, 1),
                    'incertidumbre': round(incertidumbre, 1),
                    'mensaje': f'Alta incertidumbre: ±{incertidumbre:.1f} llamadas ({incertidumbre/prediccion*100:.1f}% de la predicción)',
                    'accion': 'Monitorear de cerca, mantener personal de contingencia',
                    'confianza': 0.6
                })
            
            # Alertas por patrones de días específicos
            dia_semana = row['ds'].strftime('%A')
            if dia_semana == 'Monday' and prediccion > media_historica * 1.3:
                alertas.append({
                    'tipo': 'LUNES_ALTO',
                    'severidad': 'ALTA',
                    'fecha': fecha.isoformat(),
                    'valor_predicho': round(prediccion, 1),
                    'mensaje': f'Lunes con demanda alta: {prediccion:.1f} llamadas (efecto post-weekend)',
                    'accion': 'Reforzar equipo de lunes, preparar gestión de cola',
                    'confianza': 0.8
                })
        
        # Alertas por tendencias (cambios sostenidos)
        if len(df_predicciones) >= 5:
            ultimas_5 = df_predicciones['yhat_ensemble'].tail(5).values
            if all(ultimas_5[i] > ultimas_5[i-1] for i in range(1, len(ultimas_5))):
                alertas.append({
                    'tipo': 'TENDENCIA_CRECIENTE',
                    'severidad': 'MEDIA',
                    'fecha': df_predicciones['ds'].iloc[-1].date().isoformat(),
                    'mensaje': f'Tendencia creciente sostenida en próximos 5 días',
                    'accion': 'Revisar capacidad para siguiente semana',
                    'confianza': 0.75
                })
        
        print(f"🚨 {len(alertas)} alertas detectadas")
        
        # Ordenar por severidad y fecha
        orden_severidad = {'CRITICA': 0, 'ALTA': 1, 'MEDIA': 2, 'BAJA': 3}
        alertas.sort(key=lambda x: (orden_severidad.get(x['severidad'], 4), x['fecha']))
        
        return alertas
    
    def exportar_resultados_completos(self, df_predicciones, alertas, tipo_llamada, output_path):
        """Exporta todos los resultados del sistema multi-modelo"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Estructura de exportación completa
        resultados_completos = {
            'metadata': {
                'timestamp': timestamp,
                'tipo_llamada': tipo_llamada,
                'sistema': 'multi_modelo_ensemble',
                'modelos_utilizados': list(self.pesos_ensemble.keys()),
                'horizonte_prediccion': len(df_predicciones),
                'periodo_prediccion': f"{df_predicciones['ds'].min().date()} a {df_predicciones['ds'].max().date()}"
            },
            'configuracion': self.config,
            'pesos_ensemble': self.pesos_ensemble,
            'metadatos_modelos': self.metadatos,
            'predicciones': df_predicciones.to_dict('records'),
            'alertas': alertas,
            'resumen_estadistico': {
                'promedio_diario': float(df_predicciones['yhat_ensemble'].mean()),
                'maximo_dia': float(df_predicciones['yhat_ensemble'].max()),
                'minimo_dia': float(df_predicciones['yhat_ensemble'].min()),
                'desviacion_estandar': float(df_predicciones['yhat_ensemble'].std()),
                'total_llamadas_periodo': float(df_predicciones['yhat_ensemble'].sum()),
                'dia_pico': df_predicciones.loc[df_predicciones['yhat_ensemble'].idxmax(), 'ds'].strftime('%A %Y-%m-%d'),
                'alertas_criticas': len([a for a in alertas if a.get('severidad') == 'CRITICA']),
                'alertas_altas': len([a for a in alertas if a.get('severidad') == 'ALTA'])
            }
        }
        
        # Guardar JSON completo
        filename_json = f"{output_path}/predicciones_multimodelo_{tipo_llamada.lower()}_{timestamp}.json"
        with open(filename_json, 'w', encoding='utf-8') as f:
            json.dump(resultados_completos, f, indent=2, ensure_ascii=False, default=str)
        
        # Guardar CSV simplificado
        df_csv = df_predicciones[['ds', 'yhat_ensemble', 'yhat_lower', 'yhat_upper']].copy()
        df_csv.columns = ['fecha', 'prediccion', 'limite_inferior', 'limite_superior']
        filename_csv = f"{output_path}/predicciones_multimodelo_{tipo_llamada.lower()}_{timestamp}.csv"
        df_csv.to_csv(filename_csv, index=False, encoding='utf-8-sig')
        
        # Guardar modelos entrenados
        filename_modelos = f"{output_path}/modelos_multimodelo_{tipo_llamada.lower()}_{timestamp}.pkl"
        with open(filename_modelos, 'wb') as f:
            pickle.dump({
                'modelos': self.modelos,
                'metadatos': self.metadatos,
                'pesos_ensemble': self.pesos_ensemble,
                'config': self.config
            }, f)
        
        print(f"✅ RESULTADOS EXPORTADOS:")
        print(f"   📄 JSON: {filename_json}")
        print(f"   📊 CSV: {filename_csv}")
        print(f"   🤖 Modelos: {filename_modelos}")
        
        return resultados_completos

def main():
    """Función principal del sistema multi-modelo"""
    
    print("🚀 INICIANDO SISTEMA MULTI-MODELO CEAPSI")
    print("=" * 60)
    
    # Configurar sistema
    sistema = SistemaMultiModeloCEAPSI()
    
    # Procesar cada tipo de llamada
    tipos_llamada = ['ENTRANTE', 'SALIENTE']
    
    for tipo in tipos_llamada:
        print(f"\n📞 PROCESANDO LLAMADAS {tipo}:")
        print("-" * 40)
        
        # Cargar datos
        df = sistema.cargar_datos_segmentados(tipo)
        if df is None:
            print(f"⚠️ Saltando {tipo}, datos no disponibles")
            continue
        
        # Entrenar todos los modelos
        sistema.entrenar_modelo_arima(df)
        sistema.entrenar_modelo_prophet(df)
        sistema.entrenar_modelos_ml(df)
        
        # Validación cruzada
        metricas_cv = sistema.validacion_cruzada_temporal(df)
        
        # Calcular pesos ensemble
        sistema.calcular_pesos_ensemble(metricas_cv)
        
        # Generar predicciones
        predicciones = sistema.generar_predicciones_ensemble(df, dias_futuro=28)
        
        if predicciones is not None:
            # Detectar alertas
            alertas = sistema.detectar_alertas_avanzadas(predicciones, df)
            
            # Exportar resultados
            from pathlib import Path
            output_path = Path(__file__).parent.absolute()
            sistema.exportar_resultados_completos(predicciones, alertas, tipo, output_path)
            
            print(f"\n🎯 RESUMEN {tipo}:")
            print(f"   📊 Promedio predicho: {predicciones['yhat_ensemble'].mean():.1f} llamadas/día")
            print(f"   📈 Día pico: {predicciones.loc[predicciones['yhat_ensemble'].idxmax(), 'ds'].strftime('%A')}")
            print(f"   🚨 Alertas: {len(alertas)} detectadas")
    
    print("\n🎉 SISTEMA MULTI-MODELO COMPLETADO EXITOSAMENTE")

if __name__ == "__main__":
    main()