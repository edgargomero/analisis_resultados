#!/usr/bin/env python3
"""
CEAPSI Forecasting - Entrenamiento de Modelo Prophet
Entrena modelo Prophet con datos de CEAPSI y regresores
"""

import pandas as pd
import numpy as np
import json
import pickle
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')
import os

# Ruta base donde están las carpetas de resultados
base_resultados = r"C:\Users\edgar\OneDrive\Documentos\BBDD CEAPSI\claude\analisis_resultados"

# Buscar todas las subcarpetas que empiecen con 'resultados_'
subcarpetas = [d for d in os.listdir(base_resultados) if d.startswith('resultados_') and os.path.isdir(os.path.join(base_resultados, d))]
if not subcarpetas:
    raise FileNotFoundError("No se encontraron carpetas de resultados en 'analisis_resultados'.")

# Ordenar por nombre (timestamp) y tomar la más reciente
subcarpetas.sort()
ultima_carpeta = subcarpetas[-1]
ruta_ultima = os.path.join(base_resultados, ultima_carpeta)

# Ruta al archivo datos_prophet.csv más reciente
datos_path = os.path.join(ruta_ultima, "datos_prophet.csv")
metadatos_path = os.path.join(ruta_ultima, "metadatos_prophet.json")
print(f"📂 Usando datos Prophet de: {datos_path}")

try:
    from prophet import Prophet
    from prophet.diagnostics import cross_validation, performance_metrics
    PROPHET_AVAILABLE = True
except ImportError:
    print("⚠️ Prophet no está instalado. Instalar con: pip install prophet")
    PROPHET_AVAILABLE = False

class CeapsiProphetTrainer:
    """Clase para entrenar modelo Prophet para CEAPSI"""
    
    def __init__(self, datos_prophet_path, metadatos_path):
        self.datos_path = datos_prophet_path
        self.metadatos_path = metadatos_path
        self.df_prophet = None
        self.model = None
        self.regresores = []
        self.metadatos = {}
        self.forecast = None
        
    def cargar_datos(self):
        """Carga datos preparados para Prophet"""
        try:
            # Cargar DataFrame
            self.df_prophet = pd.read_csv(self.datos_path)
            self.df_prophet['ds'] = pd.to_datetime(self.df_prophet['ds'])
            
            # Cargar metadatos
            with open(self.metadatos_path, 'r', encoding='utf-8') as f:
                self.metadatos = json.load(f)
            
            self.regresores = self.metadatos['regresores']
            
            print(f"✅ Datos cargados:")
            print(f"   📅 Período: {self.df_prophet['ds'].min()} a {self.df_prophet['ds'].max()}")
            print(f"   📊 Registros: {len(self.df_prophet)}")
            print(f"   🔧 Regresores: {len(self.regresores)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error cargando datos: {e}")
            return False
    
    def entrenar_modelo(self):
        """Entrena el modelo Prophet"""
        
        if not PROPHET_AVAILABLE:
            print("❌ Prophet no disponible")
            return False
        
        try:
            print("🚀 Iniciando entrenamiento del modelo...")
            
            # Configurar modelo
            self.model = Prophet(
                yearly_seasonality=False,
                weekly_seasonality=True,
                daily_seasonality=False,
                changepoint_prior_scale=0.1,
                seasonality_prior_scale=15,
                holidays_prior_scale=15,
                interval_width=0.8
            )
            
            # Agregar regresores
            for regresor in self.regresores:
                if regresor in self.df_prophet.columns:
                    self.model.add_regressor(regresor, prior_scale=10)
            
            # Entrenar
            self.model.fit(self.df_prophet)
            
            print(f"✅ Modelo entrenado exitosamente")
            return True
            
        except Exception as e:
            print(f"❌ Error en entrenamiento: {e}")
            return False
    
    def guardar_modelo(self, output_path):
        """Guarda el modelo entrenado y sus metadatos"""
        
        if self.model is None:
            print("❌ No hay modelo para guardar")
            return False
        
        try:
            # Guardar modelo Prophet
            modelo_path = f"{output_path}/modelo_prophet.pkl"
            with open(modelo_path, 'wb') as f:
                pickle.dump(self.model, f)
            
            # Crear metadatos del modelo
            metadatos_modelo = {
                'fecha_entrenamiento': datetime.now().isoformat(),
                'regresores_utilizados': self.regresores,
                'periodo_entrenamiento': {
                    'inicio': self.df_prophet['ds'].min().isoformat(),
                    'fin': self.df_prophet['ds'].max().isoformat(),
                    'total_dias': len(self.df_prophet)
                },
                'parametros_modelo': {
                    'yearly_seasonality': False,
                    'weekly_seasonality': True,
                    'daily_seasonality': False,
                    'changepoint_prior_scale': 0.1,
                    'seasonality_prior_scale': 15,
                    'holidays_prior_scale': 15,
                    'interval_width': 0.8
                },
                'componentes_modelo': {
                    'trend': True,
                    'weekly': True,
                    'regresores': len(self.regresores)
                },
                'estadisticas_entrenamiento': {
                    'promedio_y': float(self.df_prophet['y'].mean()),
                    'desviacion_y': float(self.df_prophet['y'].std()),
                    'min_y': float(self.df_prophet['y'].min()),
                    'max_y': float(self.df_prophet['y'].max())
                }
            }
            
            # Guardar metadatos
            metadatos_path = f"{output_path}/metadatos_modelo.json"
            with open(metadatos_path, 'w', encoding='utf-8') as f:
                json.dump(metadatos_modelo, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Modelo guardado:")
            print(f"   📁 Modelo: {modelo_path}")
            print(f"   📄 Metadatos: {metadatos_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error guardando modelo: {e}")
            return False
    
    def validar_modelo(self):
        """Valida el modelo entrenado con validación cruzada"""
        
        if self.model is None:
            print("❌ No hay modelo para validar")
            return False
        
        try:
            print("🔍 Validando modelo con validación cruzada...")
            
            # Configurar validación cruzada
            df_cv = cross_validation(
                self.model, 
                initial='60 days', 
                period='7 days', 
                horizon='14 days'
            )
            
            # Calcular métricas
            df_performance = performance_metrics(df_cv)
            
            print(f"📊 Métricas de validación:")
            print(f"   MAE: {df_performance['mae'].mean():.2f}")
            print(f"   MAPE: {df_performance['mape'].mean():.2f}")
            print(f"   RMSE: {df_performance['rmse'].mean():.2f}")
            
            # Guardar métricas
            metricas = {
                'mae': float(df_performance['mae'].mean()),
                'mape': float(df_performance['mape'].mean()),
                'rmse': float(df_performance['rmse'].mean()),
                'validacion_cruzada': df_cv.to_dict('records')
            }
            
            return metricas
            
        except Exception as e:
            print(f"⚠️ Error en validación: {e}")
            return None

def main():
    """Función principal de entrenamiento"""
    
    if not PROPHET_AVAILABLE:
        print("❌ Prophet no está disponible. Instalar con: pip install prophet")
        return
    
    print("🤖 INICIANDO ENTRENAMIENTO DE MODELO PROPHET")
    print("=" * 60)
    
    # Rutas
    # base_path = r"C:\Users\edgar\OneDrive\Documentos\BBDD CEAPSI\claude\analisis_resultados\forecasting"
    # datos_path = f"{base_path}/datos_prophet.csv"
    # metadatos_path = f"{base_path}/metadatos_prophet.json"
    
    # Crear entrenador
    trainer = CeapsiProphetTrainer(datos_path, metadatos_path)
    
    # Ejecutar entrenamiento completo
    if trainer.cargar_datos():
        if trainer.entrenar_modelo():
            
            # Validar modelo (opcional)
            print("\n🔍 Validando modelo...")
            metricas = trainer.validar_modelo()
            
            # Guardar modelo
            print("\n💾 Guardando modelo...")
            if trainer.guardar_modelo(ruta_ultima):
                print("\n🎉 ENTRENAMIENTO COMPLETADO EXITOSAMENTE")
                print(f"   📁 Modelo guardado en: {ruta_ultima}/modelo_prophet.pkl")
                print(f"   📄 Metadatos guardados en: {ruta_ultima}/metadatos_modelo.json")
                
                if metricas:
                    print(f"\n📊 Métricas de validación:")
                    print(f"   MAE: {metricas['mae']:.2f}")
                    print(f"   MAPE: {metricas['mape']:.2f}")
                    print(f"   RMSE: {metricas['rmse']:.2f}")
            else:
                print("❌ Error guardando modelo")
        else:
            print("❌ Error en entrenamiento")
    else:
        print("❌ Error cargando datos")

if __name__ == "__main__":
    main()
